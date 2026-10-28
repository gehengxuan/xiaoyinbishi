import json
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from knowledge_agent.agent import Agent
from knowledge_agent.knowledge import KnowledgeBase
from knowledge_agent.mock_model import OfflineMockModel
from knowledge_agent.tools import ToolExecutor
from knowledge_agent.types import Action, Request

ROOT = Path(__file__).resolve().parents[1]


def knowledge() -> KnowledgeBase:
    return KnowledgeBase(ROOT / "data/knowledge_base.json", ROOT / "data/synonyms.json")


def run(question="正式员工一年有多少天带薪年假？", *, history=None, faults=None, model=None, kb=None, **limits):
    agent = Agent(model or OfflineMockModel(), ToolExecutor(kb or knowledge(), faults), **limits)
    return agent.run(Request.from_dict({"question": question, "history": history or []}))


def search(query="年假", limit=5):
    return "search_documents", {"query": query, "limit": limit, "reason": "测试：检索资料。"}


def read(doc_id="D03"):
    return "read_document", {"document_id": doc_id, "reason": "测试：读取原文。"}


def citation(doc_id="D03", chunk_id="C01", quote="正式员工每年享有 10 天带薪年假。"):
    return {"document_id": doc_id, "chunk_id": chunk_id, "quote": quote}


def finish(status="answered", citations=None, gaps=None, follow_up=""):
    return "finish", {
        "status": status,
        "citations": [citation()] if citations is None else citations,
        "gaps": gaps or [],
        "follow_up_question": follow_up,
        "reason": "测试：根据实际证据选择结束状态。",
    }


class ScriptedModel:
    """Test double: verifies runtime mechanics, never used as model evidence."""

    name = "scripted-test-double"
    execution_mode = "test_stub"

    def __init__(self, actions):
        self.actions = iter(actions)
        self.messages_seen = []

    def choose(self, messages, tools):
        self.messages_seen.append(json.loads(json.dumps(messages)))
        value = next(self.actions)
        if isinstance(value, Exception):
            raise value
        return Action(value[0], value[1], f"test_call_{len(self.messages_seen)}")


@contextmanager
def variant(overrides):
    data = json.loads((ROOT / "data/knowledge_base.json").read_text(encoding="utf-8"))
    for doc_id, chunk_id, text in overrides:
        doc = next(doc for doc in data["documents"] if doc["document_id"] == doc_id)
        next(chunk for chunk in doc["chunks"] if chunk["chunk_id"] == chunk_id)["text"] = text
    with TemporaryDirectory() as directory:
        path = Path(directory) / "corpus.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        yield KnowledgeBase(path, ROOT / "data/synonyms.json")


def error_codes(trace):
    return [event["observation"]["error"]["code"] for event in trace if "error" in event.get("observation", {})]
