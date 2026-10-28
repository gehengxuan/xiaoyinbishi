"""Tool schemas, argument checks, and deterministic fault injection."""

from dataclasses import dataclass
from typing import Any

from .knowledge import KnowledgeBase


def object_schema(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def function(name: str, description: str, properties: dict) -> dict:
    return {"type": "function", "function": {
        "name": name,
        "description": description,
        "strict": True,
        "parameters": object_schema(properties | {
            "reason": {"type": "string", "description": "一句简短的可公开动作依据，不要输出内部思维过程。"},
        }),
    }}


TOOL_SCHEMAS = [
    function("search_documents", "按问题或改写查询检索文档元数据；结果不是原文证据，可再次检索查证适用范围或优先级。", {
        "query": {"type": "string"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 10},
    }),
    function("read_document", "读取指定文档的短原文片段、版本日期和适用范围。引用前必须调用本工具。", {
        "document_id": {"type": "string"},
    }),
    function("finish", "提交有证据的结果或明确追问/停止。程序只从通过校验的原文片段渲染事实答案。", {
        "status": {"type": "string", "enum": ["answered", "needs_clarification", "not_found", "tool_error"]},
        "citations": {"type": "array", "items": object_schema({
            "document_id": {"type": "string"},
            "chunk_id": {"type": "string"},
            "quote": {"type": "string", "description": "必须逐字复制已经读到的完整短片段 text。"},
        })},
        "gaps": {"type": "array", "items": {"type": "string"}},
        "follow_up_question": {"type": "string", "description": "需要澄清时填写具体问题；否则使用空字符串。"},
    }),
]


def error(code: str, message: str, retryable: bool = False, **details: Any) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, "retryable": retryable, **details}}


def validate_arguments(name: str, arguments: Any) -> str | None:
    schema = next((item["function"]["parameters"] for item in TOOL_SCHEMAS if item["function"]["name"] == name), None)
    if schema is None:
        return "工具不在允许列表中。"
    if not isinstance(arguments, dict) or set(arguments) != set(schema["properties"]):
        return "工具参数字段必须与 schema 完全一致。"
    reason = arguments.get("reason")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 400:
        return "reason 必须是 1–400 字的简短依据。"
    if name == "search_documents":
        if not isinstance(arguments["query"], str) or not arguments["query"].strip() or len(arguments["query"]) > 2000:
            return "query 必须是 1–2000 字。"
        if type(arguments["limit"]) is not int or not 1 <= arguments["limit"] <= 10:
            return "limit 必须是 1–10 的整数。"
    if name == "read_document":
        if not isinstance(arguments["document_id"], str) or not arguments["document_id"].strip():
            return "document_id 必须是非空字符串。"
    if name == "finish":
        if arguments["status"] not in ("answered", "needs_clarification", "not_found", "tool_error"):
            return "status 不合法。"
        for field in ("citations", "gaps"):
            if not isinstance(arguments[field], list) or len(arguments[field]) > 30:
                return f"{field} 必须是最多 30 项的数组。"
        if any(not isinstance(gap, str) or not gap.strip() or len(gap) > 1000 for gap in arguments["gaps"]):
            return "gaps 必须是非空短字符串数组。"
        if not isinstance(arguments["follow_up_question"], str) or len(arguments["follow_up_question"]) > 1000:
            return "follow_up_question 必须是短字符串。"
        for citation in arguments["citations"]:
            if not isinstance(citation, dict) or set(citation) != {"document_id", "chunk_id", "quote"} or any(
                not isinstance(value, str) or not value.strip() for value in citation.values()
            ):
                return "引用必须包含非空 document_id、chunk_id、quote。"
    return None


@dataclass
class Fault:
    tool: str
    remaining: int  # -1 means persistent; positive means fail the next N matching calls.
    document_id: str | None = None

    @classmethod
    def from_dict(cls, value: dict) -> "Fault":
        if not isinstance(value, dict) or set(value) - {"tool", "remaining", "document_id"}:
            raise ValueError("故障配置字段不合法。")
        tool, remaining, doc_id = value.get("tool"), value.get("remaining"), value.get("document_id")
        if tool not in ("search_documents", "read_document") or type(remaining) is not int or remaining < -1:
            raise ValueError("故障 tool 或 remaining 不合法。")
        if doc_id is not None and (tool != "read_document" or not isinstance(doc_id, str) or not doc_id):
            raise ValueError("document_id 只能用于 read_document 故障。")
        return cls(tool, remaining, doc_id)

    def to_dict(self) -> dict:
        return {"tool": self.tool, "remaining": self.remaining, "document_id": self.document_id}


class ToolExecutor:
    def __init__(self, knowledge: KnowledgeBase, faults: list[Fault] | None = None):
        self.knowledge = knowledge
        # Own the counters; repeated runs never share mutated fault state.
        self.faults = [Fault(item.tool, item.remaining, item.document_id) for item in (faults or [])]
        self.initial_faults = [item.to_dict() for item in self.faults]

    def execute(self, name: str, arguments: dict) -> dict:
        message = validate_arguments(name, arguments)
        if message:
            return error("INVALID_ARGUMENTS", message)
        for fault in self.faults:
            if fault.tool == name and fault.remaining != 0 and (
                fault.document_id is None or fault.document_id == arguments.get("document_id")
            ):
                if fault.remaining > 0:
                    fault.remaining -= 1
                return error("INJECTED_TOOL_FAILURE", "合成工具暂时不可用；本次调用未返回资料。", retryable=True)
        if name == "search_documents":
            return self.knowledge.search(arguments["query"], arguments["limit"])
        if name == "read_document":
            return self.knowledge.read(arguments["document_id"])
        return error("UNKNOWN_TOOL", "工具不可执行。")
