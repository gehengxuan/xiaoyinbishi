"""Deterministic observation-driven fixture, NOT an LLM or ReAct quality proof.

It can only see the same messages/tools as a live provider. It cannot access the
corpus, expected test results, case IDs, or pre-recorded traces.
"""

import json
import re
from collections import defaultdict

from .knowledge import normalized, terms
from .types import Action


class OfflineMockModel:
    name = "offline-observation-mock-v1"
    execution_mode = "offline_mock"

    def __init__(self):
        self.counter = 0

    def _action(self, name: str, **arguments) -> Action:
        self.counter += 1
        return Action(name, arguments, f"mock_call_{self.counter}")

    def _finish(self, status: str, citations: list[dict], gaps: list[str], follow_up: str, reason: str) -> Action:
        return self._action("finish", status=status, citations=citations, gaps=gaps, follow_up_question=follow_up, reason=reason)

    def choose(self, messages: list[dict], tools: list[dict]) -> Action:
        task = json.loads(next(message["content"] for message in messages if message["role"] == "user"))
        question = task["question"]
        context = " ".join(item["content"] for item in task.get("history", []) if item["role"] == "user")
        initial_query = (context + " " + question).strip()
        calls = {}
        observations = []
        for message in messages:
            for call in message.get("tool_calls", []):
                calls[call["id"]] = (call["function"]["name"], json.loads(call["function"]["arguments"]))
            if message["role"] == "tool":
                name, arguments = calls[message["tool_call_id"]]
                observations.append((name, arguments, json.loads(message["content"])))

        reads = {result["document_id"]: result for name, _, result in observations if name == "read_document" and result.get("ok")}
        searches = [(arguments, result) for name, arguments, result in observations if name == "search_documents" and result.get("ok")]
        if not observations:
            if not context and normalized(question).strip("？?。！!") in {"那个呢", "这个呢", "怎么办", "多久", "多少天", "你好", "帮我查一下"}:
                return self._finish("needs_clarification", [], ["问题没有说明要查询的制度或产品事项。"], "你要查询哪项制度或产品功能？", "缺少可检索的主题，先请求补充。")
            return self._action("search_documents", query=initial_query, limit=5, reason="先检索与问题及对话上下文有关的文档。")

        last_name, last_arguments, last_result = observations[-1]
        if not last_result.get("ok"):
            problem = last_result["error"]
            if problem["code"] == "EVIDENCE_INCOMPLETE":
                return self._action("read_document", document_id=problem["missing_document_ids"][0], reason="校验发现同主题候选资料尚未读取，补读后再判断。")
            failed_count = sum(
                1 for name, args, result in observations
                if name == last_name and not result.get("ok")
                and (name != "read_document" or args.get("document_id") == last_arguments.get("document_id"))
            )
            if last_name in ("search_documents", "read_document") and problem.get("retryable") and failed_count < 2:
                retry_arguments = {key: value for key, value in last_arguments.items() if key != "reason"}
                return self._action(last_name, **retry_arguments, reason="观察到可恢复工具错误，选择再试一次；已有结果仍保留。")
            return self._finish("tool_error", self._all_citations(reads), ["部分资料因工具连续失败而未能取得。"], "", "工具仍不可用，保留已读证据并明确停止。")

        primary = next((result["hits"][0] for _, result in searches if result["hits"]), None)
        if primary:
            for doc_id in primary["related_document_ids"]:
                if doc_id not in reads:
                    return self._action("read_document", document_id=doc_id, reason="命中资料只是线索，需要读取原文及同主题候选文档。")

        if not primary:
            if len(searches) < 2:
                rewritten = re.sub(r"请问|公司|能否|是否|提供|可以|吗|呢|[？?。！!]", "", question).strip()
                if not rewritten or normalized(rewritten) == normalized(initial_query):
                    rewritten = "查询 " + initial_query
                return self._action("search_documents", query=rewritten, limit=5, reason="首次检索无命中，删去问句修饰词后补充检索。")
            return self._finish("not_found", [], ["当前合成知识库没有支持该问题的资料。"], "可以补充对应制度或产品文档吗？", "改写查询后仍无资料，停止并说明缺口。")

        conflicts = self._conflicts(reads)
        if conflicts:
            if not any("优先级" in args["query"] and "适用范围" in args["query"] for args, _ in searches):
                titles = " ".join(doc["title"] for doc in reads.values())
                return self._action("search_documents", query=titles + " 适用范围 优先级", limit=5, reason="读到不同政策表述，补查适用范围和优先级依据。")
            scope = sorted(conflicts)[0][0]
            citations = [cite for cite in self._all_citations(reads) if (reads[cite["document_id"]]["scope"], self._policy_key(reads, cite)) in conflicts]
            return self._finish(
                "needs_clarification", citations,
                ["同一主题存在不同原文表述，资料未注明优先级或替代关系。", f"需要确认适用范围（当前标注：{scope}）。"],
                "请确认适用部门及应以哪份制度为准，或补充明确的优先级/废止说明。",
                "查证后仍缺少消解冲突的依据，列出各方原文并请求确认。",
            )

        citations = self._all_citations(reads)
        current_terms = terms(question)
        best = max(citations, key=lambda cite: len(current_terms & terms(cite["quote"])))
        return self._finish("answered", [best], [], "", "已读取相关原文，未发现同主题同范围的不同表述，引用原文作答。")

    @staticmethod
    def _all_citations(reads: dict) -> list[dict]:
        return [
            {"document_id": doc_id, "chunk_id": chunk["chunk_id"], "quote": chunk["text"]}
            for doc_id, doc in reads.items() for chunk in doc["chunks"]
        ]

    @staticmethod
    def _policy_key(reads: dict, cite: dict) -> str:
        return next(chunk["policy_key"] for chunk in reads[cite["document_id"]]["chunks"] if chunk["chunk_id"] == cite["chunk_id"])

    @staticmethod
    def _conflicts(reads: dict) -> set[tuple[str, str]]:
        groups = defaultdict(set)
        for doc in reads.values():
            for chunk in doc["chunks"]:
                groups[(doc["scope"], chunk["policy_key"])].add(normalized(chunk["text"]))
        return {key for key, texts in groups.items() if len(texts) > 1}
