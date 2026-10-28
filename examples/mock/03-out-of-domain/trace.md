# 执行记录：公司提供火星移民补贴吗？

- 模式：`offline_mock`
- 模型/替身：`offline-observation-mock-v1`
- 状态：`not_found`
- 知识库 SHA256：`b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66`

> 仅验证流程，不能证明真实模型的 ReAct 决策效果。

## 记录 1

动作：`search_documents`；已执行：`True`

公开依据：先检索与问题及对话上下文有关的文档。

参数：

```json
{
  "query": "公司提供火星移民补贴吗？",
  "limit": 5,
  "reason": "先检索与问题及对话上下文有关的文档。"
}
```

返回摘要：命中 0 份；返回 []；has_more=False

后续动作：`search_documents`

## 记录 2

动作：`search_documents`；已执行：`True`

公开依据：首次检索无命中，删去问句修饰词后补充检索。

参数：

```json
{
  "query": "火星移民补贴",
  "limit": 5,
  "reason": "首次检索无命中，删去问句修饰词后补充检索。"
}
```

返回摘要：命中 0 份；返回 []；has_more=False

后续动作：`finish`

## 记录 3

动作：`finish`；已执行：`True`

公开依据：改写查询后仍无资料，停止并说明缺口。

参数：

```json
{
  "status": "not_found",
  "citations": [],
  "gaps": [
    "当前合成知识库没有支持该问题的资料。"
  ],
  "follow_up_question": "可以补充对应制度或产品文档吗？",
  "reason": "改写查询后仍无资料，停止并说明缺口。"
}
```

返回摘要：最终状态 not_found；有效引用 0 个。

后续：结束，状态 `not_found`。

## 实际输出

```json
{
  "status": "not_found",
  "answer": "在当前知识库中未找到足以回答问题的资料。",
  "citations": [],
  "conflicts": [],
  "gaps": [
    "当前合成知识库没有支持该问题的资料。"
  ],
  "follow_up_question": "可以补充对应制度或产品文档吗？",
  "stop_reason": "改写查询后仍无资料，停止并说明缺口。",
  "question": "公司提供火星移民补贴吗？",
  "run": {
    "run_id": "b49a4deb-97ba-4459-bbd1-e279edb50379",
    "execution_mode": "offline_mock",
    "model": "offline-observation-mock-v1",
    "mock_boundary": "仅验证流程，不能证明真实模型的 ReAct 决策效果。",
    "corpus_version": "synthetic-2026-10-28-v1",
    "corpus_sha256": "b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66",
    "model_calls": 3,
    "tool_calls": 3,
    "max_steps": 14,
    "max_tool_calls": 12,
    "started_at": "2026-10-28T13:15:46.727+00:00",
    "finished_at": "2026-10-28T13:15:46.727+00:00",
    "duration_ms": 0.283
  }
}
```
