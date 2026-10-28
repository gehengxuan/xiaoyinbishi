"""CLI entry point. Run from the repository root with PYTHONPATH=src."""

import argparse
import json
import sys
from pathlib import Path

from .agent import Agent
from .config import environment
from .knowledge import KnowledgeBase
from .mock_model import OfflineMockModel
from .model import DeepSeekModel, OpenAICompatibleModel
from .recording import save_run
from .tools import Fault, ToolExecutor
from .types import Request


def parse_fault(value: str) -> Fault:
    parts = value.split(":")
    if len(parts) not in (2, 3):
        raise ValueError("故障格式：TOOL[:DOCUMENT_ID]:COUNT，COUNT 可为 always。")
    count = -1 if parts[-1] == "always" else int(parts[-1])
    return Fault.from_dict({"tool": parts[0], "remaining": count, "document_id": parts[1] if len(parts) == 3 else None})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="项目题 3：企业知识问答 Agent（默认离线 Mock，非真实模型效果证明）")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--question", help="当前问题")
    source.add_argument("--input", type=Path, help="包含 question 与可选 history 的 JSON 文件")
    parser.add_argument("--provider", choices=("mock", "deepseek", "openai"), default="mock")
    parser.add_argument("--env-file", type=Path, help="可选本地 KEY=value 文件，不执行 shell 代码；请勿提交密钥")
    parser.add_argument("--corpus", type=Path, default=Path("data/knowledge_base.json"))
    parser.add_argument("--synonyms", type=Path, default=Path("data/synonyms.json"))
    parser.add_argument("--max-steps", type=int, default=14)
    parser.add_argument("--max-tool-calls", type=int, default=12)
    parser.add_argument("--fail-tool", action="append", default=[], metavar="TOOL[:DOC]:COUNT")
    parser.add_argument("--output-dir", type=Path, default=Path("runs/latest"))
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.input.read_text(encoding="utf-8")) if args.input else {"question": args.question}
        request = Request.from_dict(value)
        knowledge = KnowledgeBase(args.corpus, args.synonyms)
        faults = [parse_fault(value) for value in args.fail_tool]
        if args.provider == "mock":
            model = OfflineMockModel()
        else:
            provider_class = DeepSeekModel if args.provider == "deepseek" else OpenAICompatibleModel
            model = provider_class.from_env(environment(args.env_file))
        agent = Agent(model, ToolExecutor(knowledge, faults), args.max_steps, args.max_tool_calls)
    except (ValueError, OSError) as exc:
        message = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError) else "无法读取有效的输入或知识库 JSON 文件。"
        print(json.dumps({"status": "invalid_input", "gaps": [message]}, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.provider == "mock":
        print("OFFLINE MOCK：仅验证流程，不能证明真实模型的 ReAct 决策效果。", file=sys.stderr)
    result, trace = agent.run(request)
    try:
        save_run(args.output_dir, request, result, trace, {
            "provider": args.provider,
            "corpus_file": args.corpus.name,
            "synonyms_file": args.synonyms.name,
            "faults": [fault.to_dict() for fault in faults],
            "max_steps": args.max_steps,
            "max_tool_calls": args.max_tool_calls,
        })
    except OSError:
        print("执行已结束，但运行记录写入失败；请检查 --output-dir。", file=sys.stderr)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 4
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return {"answered": 0, "needs_clarification": 3, "not_found": 3, "tool_error": 4, "model_error": 4, "limit_reached": 5}[result["status"]]
