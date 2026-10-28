"""Persist actual inputs, outputs and public action/observation records."""

import json
from pathlib import Path

from .types import Request


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_run(directory: Path, request: Request, result: dict, trace: list[dict], config: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "input.json", request.to_dict())
    write_json(directory / "output.json", result)
    write_json(directory / "trace.json", trace)
    write_json(directory / "run-config.json", config)
    lines = [
        f"# 执行记录：{result['question']}", "",
        f"- 模式：`{result['run']['execution_mode']}`",
        f"- 模型/替身：`{result['run']['model']}`",
        f"- 状态：`{result['status']}`",
        f"- 知识库 SHA256：`{result['run']['corpus_sha256']}`", "",
    ]
    if result["run"]["mock_boundary"]:
        lines += ["> " + result["run"]["mock_boundary"], ""]
    for index, event in enumerate(trace):
        lines += [f"## 记录 {index + 1}", ""]
        if "action" in event:
            action = event["action"]
            lines += [
                f"动作：`{action['tool']}`；已执行：`{event['executed']}`", "",
                "公开依据：" + str(event["decision_summary"]), "",
                "参数：", "", "```json",
                json.dumps(action["arguments"], ensure_ascii=False, indent=2), "```", "",
            ]
        else:
            lines += [f"事件：`{event['event']}`", ""]
        observation = event.get("observation", {})
        summary = event.get("return_summary") or observation.get("error", {}).get("message", "")
        lines += ["返回摘要：" + summary, ""]
        for chunk in observation.get("chunks", []):
            lines += [f"> [{observation['document_id']}/{chunk['chunk_id']}] {chunk['text']}", ""]
        next_action = next((item["action"]["tool"] for item in trace[index + 1:] if "action" in item), None)
        lines += [f"后续动作：`{next_action}`" if next_action else f"后续：结束，状态 `{result['status']}`。", ""]
    lines += ["## 实际输出", "", "```json", json.dumps(result, ensure_ascii=False, indent=2), "```", ""]
    (directory / "trace.md").write_text("\n".join(lines), encoding="utf-8")
