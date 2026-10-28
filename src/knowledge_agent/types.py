"""Small, explicit contracts shared by the model, runtime, and CLI."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Request:
    question: str
    history: tuple[dict[str, str], ...] = ()

    @classmethod
    def from_dict(cls, value: Any) -> "Request":
        if not isinstance(value, dict) or set(value) - {"question", "history"}:
            raise ValueError("输入只能包含 question 和可选 history。")
        question = value.get("question")
        if not isinstance(question, str) or not question.strip() or len(question) > 2000:
            raise ValueError("question 必须是 1–2000 字的非空字符串。")
        history = value.get("history", [])
        if not isinstance(history, list) or len(history) > 10:
            raise ValueError("history 必须是最多 10 条消息的数组。")
        clean = []
        for item in history:
            if (
                not isinstance(item, dict)
                or set(item) != {"role", "content"}
                or item["role"] not in ("user", "assistant")
                or not isinstance(item["content"], str)
                or not item["content"].strip()
                or len(item["content"]) > 2000
            ):
                raise ValueError("历史只接受 role=user/assistant、1–2000 字的 content。")
            clean.append(dict(item))
        return cls(question.strip(), tuple(clean))

    def to_dict(self) -> dict[str, Any]:
        return {"question": self.question, "history": list(self.history)}


@dataclass(frozen=True)
class Action:
    name: str
    arguments: dict[str, Any]
    call_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def assistant_message(self) -> dict[str, Any]:
        import json

        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": self.call_id,
                "type": "function",
                "function": {
                    "name": self.name,
                    "arguments": json.dumps(self.arguments, ensure_ascii=False),
                },
            }],
        }


class ModelError(Exception):
    """A sanitized transport/configuration error. Never includes credentials."""


class ModelProtocolError(ModelError):
    """The model's response cannot be interpreted as exactly one action."""


class Model(Protocol):
    name: str
    execution_mode: str

    def choose(self, messages: list[dict], tools: list[dict]) -> Action: ...
