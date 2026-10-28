"""Run actual cases and record results; expected answers never enter model messages."""

import argparse
import json
from pathlib import Path

from knowledge_agent.agent import Agent, utc_now
from knowledge_agent.config import environment
from knowledge_agent.knowledge import KnowledgeBase
from knowledge_agent.mock_model import OfflineMockModel
from knowledge_agent.model import DeepSeekModel
from knowledge_agent.recording import save_run, write_json
from knowledge_agent.tools import Fault, ToolExecutor
from knowledge_agent.types import Request


def checks_for(case: dict, result: dict, trace: list[dict], knowledge: KnowledgeBase) -> list[dict]:
    checks = []

    def check(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": bool(passed)})

    expected = case["expected"]
    check("任务状态", result["status"] == expected["status"])
    check("引用文档集合", {cite["document_id"] for cite in result["citations"]} == set(expected["citation_ids"]))
    for text in expected.get("answer_contains", []):
        check("答案包含 " + text, text in result["answer"])
    for text in expected.get("answer_excludes", []):
        check("答案不含 " + text, text not in result["answer"])
    if "conflict_count" in expected:
        check("冲突组数", len(result["conflicts"]) == expected["conflict_count"])
    failed = sum(1 for event in trace if event.get("action", {}).get("tool") in ("search_documents", "read_document") and not event.get("observation", {}).get("ok"))
    check("故障实际触发", failed >= expected.get("min_failed_tools", 0))
    searches = sum(1 for event in trace if event.get("action", {}).get("tool") == "search_documents" and event.get("observation", {}).get("ok"))
    check("实际检索次数", searches >= expected.get("min_successful_searches", 0))
    successful_reads = {
        event["observation"]["document_id"]
        for event in trace if event.get("action", {}).get("tool") == "read_document" and event.get("observation", {}).get("ok")
    }
    check("引用来自实际成功读取的原文", all(
        cite["document_id"] in successful_reads
        and any(chunk["chunk_id"] == cite["chunk_id"] and chunk["text"] == cite["quote"] for chunk in knowledge.documents[cite["document_id"]]["chunks"])
        and cite["version_date"] == knowledge.documents[cite["document_id"]]["version_date"]
        for cite in result["citations"]
    ))
    check("调用次数有界", result["run"]["model_calls"] <= result["run"]["max_steps"] and result["run"]["tool_calls"] <= result["run"]["max_tool_calls"])
    if result["status"] == "needs_clarification":
        check("具体追问和资料缺口", bool(result["follow_up_question"].strip()) and bool(result["gaps"]))
    if result["status"] != "answered":
        check("未回答状态说明缺口", bool(result["gaps"]))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="运行验收集并保存实际输出/Trace；Mock 成绩不等于真实模型成绩。")
    parser.add_argument("--provider", choices=("mock", "deepseek"), default="mock")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--cases", type=Path, default=Path("examples/cases.json"))
    parser.add_argument("--case", action="append", dest="case_ids", help="可重复指定单个 case ID")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    directory = args.output_dir or Path("examples/mock" if args.provider == "mock" else "examples/live")
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if args.case_ids:
        known = {case["id"] for case in cases}
        if set(args.case_ids) - known:
            parser.error("--case 中存在未知 ID。")
        cases = [case for case in cases if case["id"] in args.case_ids]
    env = environment(args.env_file) if args.provider == "deepseek" else None
    # Fail before producing any misleading 'live' artifacts if credentials/config are missing.
    if args.provider == "deepseek":
        try:
            DeepSeekModel.from_env(env)
        except ValueError as exc:
            parser.error(str(exc))
    directory.mkdir(parents=True, exist_ok=True)
    base_path = Path("data/knowledge_base.json")
    rows = []
    for case in cases:
        case_dir = directory / case["id"]
        corpus_path = base_path
        if case.get("overrides"):
            corpus = json.loads(base_path.read_text(encoding="utf-8"))
            corpus["corpus_version"] += ":" + case["id"]
            for override in case["overrides"]:
                doc = next(doc for doc in corpus["documents"] if doc["document_id"] == override["document_id"])
                chunk = next(chunk for chunk in doc["chunks"] if chunk["chunk_id"] == override["chunk_id"])
                chunk["text"] = override["text"]
            corpus_path = case_dir / "corpus.json"
            write_json(corpus_path, corpus)
        knowledge = KnowledgeBase(corpus_path, Path("data/synonyms.json"))
        faults = [Fault.from_dict(value) for value in case.get("faults", [])]
        model = OfflineMockModel() if args.provider == "mock" else DeepSeekModel.from_env(env)
        request = Request.from_dict(case["input"])
        max_steps, max_tools = case.get("max_steps", 14), case.get("max_tool_calls", 12)
        result, trace = Agent(model, ToolExecutor(knowledge, faults), max_steps, max_tools).run(request)
        checks = checks_for(case, result, trace, knowledge)
        save_run(case_dir, request, result, trace, {
            "provider": args.provider, "faults": [fault.to_dict() for fault in faults],
            "max_steps": max_steps, "max_tool_calls": max_tools,
            "corpus_file": "corpus.json" if case.get("overrides") else "data/knowledge_base.json",
        })
        write_json(case_dir / "checks.json", checks)
        passed = all(check["passed"] for check in checks)
        actions = [event["action"]["tool"] for event in trace if "action" in event]
        rows.append({"case_id": case["id"], "acceptance": case["acceptance"], "status": result["status"], "passed": passed, "actions": actions, "checks": checks})
        print(f"{'PASS' if passed else 'FAIL'} {case['id']}: {result['status']} ({result['run']['model_calls']} model calls)")
    passed_count = sum(row["passed"] for row in rows)
    summary = {
        "generated_at": utc_now(), "provider": args.provider,
        "evidence_boundary": "离线流程验收；真实模型效果尚未验证。" if args.provider == "mock" else "真实 API 调用记录；单次小样本结果，仍需人工检查相关性与检索完整性。",
        "total": len(rows), "passed": passed_count, "failed": len(rows) - passed_count, "cases": rows,
    }
    write_json(directory / "evaluation.json", summary)
    lines = ["# 实际验收结果", "", f"模式：`{args.provider}`；通过：{passed_count}/{len(rows)}。", "", summary["evidence_boundary"], "", "| 用例 | 状态 | 检查 | 实际动作 | 记录 |", "|---|---|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['case_id']} | {row['status']} | {'PASS' if row['passed'] else 'FAIL'} | {' → '.join(row['actions'])} | [Trace]({row['case_id']}/trace.md) |")
    (directory / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{passed_count}/{len(rows)} cases passed. Provider={args.provider}; see {directory / 'evaluation.json'}")
    return 0 if passed_count == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
