# 执行记录：正式员工一年有多少天带薪年假？

- 模式：`offline_mock`
- 模型/替身：`offline-observation-mock-v1`
- 状态：`limit_reached`
- 知识库 SHA256：`b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66`

> 仅验证流程，不能证明真实模型的 ReAct 决策效果。

## 记录 1

动作：`search_documents`；已执行：`True`

公开依据：先检索与问题及对话上下文有关的文档。

参数：

```json
{
  "query": "正式员工一年有多少天带薪年假？",
  "limit": 5,
  "reason": "先检索与问题及对话上下文有关的文档。"
}
```

返回摘要：命中 1 份；返回 ['D03']；has_more=False

后续：结束，状态 `limit_reached`。

## 记录 2

事件：`limit_reached`

返回摘要：模型决策步数达到上限。

后续：结束，状态 `limit_reached`。

## 实际输出

```json
{
  "status": "limit_reached",
  "answer": "任务未完成；已获取的资料保留在 citations，不能据此视为已回答。",
  "citations": [],
  "conflicts": [],
  "gaps": [
    "模型决策步数达到上限；任务未完成。"
  ],
  "follow_up_question": "",
  "stop_reason": "模型决策步数达到上限；任务未完成。",
  "question": "正式员工一年有多少天带薪年假？",
  "run": {
    "run_id": "b7d32170-f327-4a17-9ff5-1e670ef49ac0",
    "execution_mode": "offline_mock",
    "model": "offline-observation-mock-v1",
    "mock_boundary": "仅验证流程，不能证明真实模型的 ReAct 决策效果。",
    "corpus_version": "synthetic-2026-10-28-v1",
    "corpus_sha256": "b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66",
    "model_calls": 1,
    "tool_calls": 1,
    "max_steps": 1,
    "max_tool_calls": 12,
    "started_at": "2026-10-28T13:15:46.732+00:00",
    "finished_at": "2026-10-28T13:15:46.732+00:00",
    "duration_ms": 0.089
  }
}
```
