# 执行记录：报销材料应在多少天内提交？

- 模式：`offline_mock`
- 模型/替身：`offline-observation-mock-v1`
- 状态：`tool_error`
- 知识库 SHA256：`b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66`

> 仅验证流程，不能证明真实模型的 ReAct 决策效果。

## 记录 1

动作：`search_documents`；已执行：`True`

公开依据：先检索与问题及对话上下文有关的文档。

参数：

```json
{
  "query": "报销材料应在多少天内提交？",
  "limit": 5,
  "reason": "先检索与问题及对话上下文有关的文档。"
}
```

返回摘要：命中 2 份；返回 ['D01', 'D02']；has_more=False

后续动作：`read_document`

## 记录 2

动作：`read_document`；已执行：`True`

公开依据：命中资料只是线索，需要读取原文及同主题候选文档。

参数：

```json
{
  "document_id": "D01",
  "reason": "命中资料只是线索，需要读取原文及同主题候选文档。"
}
```

返回摘要：读到 D01 (2026-01-15) 的 1 个原文片段。

> [D01/C01] 报销材料应在费用发生后 30 天内提交。

后续动作：`read_document`

## 记录 3

动作：`read_document`；已执行：`True`

公开依据：命中资料只是线索，需要读取原文及同主题候选文档。

参数：

```json
{
  "document_id": "D02",
  "reason": "命中资料只是线索，需要读取原文及同主题候选文档。"
}
```

返回摘要：INJECTED_TOOL_FAILURE: 合成工具暂时不可用；本次调用未返回资料。

后续动作：`read_document`

## 记录 4

动作：`read_document`；已执行：`True`

公开依据：观察到可恢复工具错误，选择再试一次；已有结果仍保留。

参数：

```json
{
  "document_id": "D02",
  "reason": "观察到可恢复工具错误，选择再试一次；已有结果仍保留。"
}
```

返回摘要：INJECTED_TOOL_FAILURE: 合成工具暂时不可用；本次调用未返回资料。

后续动作：`finish`

## 记录 5

动作：`finish`；已执行：`True`

公开依据：工具仍不可用，保留已读证据并明确停止。

参数：

```json
{
  "status": "tool_error",
  "citations": [
    {
      "document_id": "D01",
      "chunk_id": "C01",
      "quote": "报销材料应在费用发生后 30 天内提交。"
    }
  ],
  "gaps": [
    "部分资料因工具连续失败而未能取得。"
  ],
  "follow_up_question": "",
  "reason": "工具仍不可用，保留已读证据并明确停止。"
}
```

返回摘要：最终状态 tool_error；有效引用 1 个。

后续：结束，状态 `tool_error`。

## 实际输出

```json
{
  "status": "tool_error",
  "answer": "工具查询未完成，暂不能可靠回答。以下引用仅为已取得的部分资料：\n- [D01/C01，2026-01-15] 报销材料应在费用发生后 30 天内提交。",
  "citations": [
    {
      "document_id": "D01",
      "title": "费用报销管理办法",
      "version_date": "2026-01-15",
      "scope": "未注明",
      "chunk_id": "C01",
      "policy_key": "expense_submission_deadline",
      "quote": "报销材料应在费用发生后 30 天内提交。"
    }
  ],
  "conflicts": [],
  "gaps": [
    "部分资料因工具连续失败而未能取得。"
  ],
  "follow_up_question": "",
  "stop_reason": "工具仍不可用，保留已读证据并明确停止。",
  "question": "报销材料应在多少天内提交？",
  "run": {
    "run_id": "5f999c9d-2ff2-4a7b-aa71-6e34616fecf4",
    "execution_mode": "offline_mock",
    "model": "offline-observation-mock-v1",
    "mock_boundary": "仅验证流程，不能证明真实模型的 ReAct 决策效果。",
    "corpus_version": "synthetic-2026-10-28-v1",
    "corpus_sha256": "b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66",
    "model_calls": 5,
    "tool_calls": 5,
    "max_steps": 14,
    "max_tool_calls": 12,
    "started_at": "2026-10-28T13:15:46.730+00:00",
    "finished_at": "2026-10-28T13:15:46.730+00:00",
    "duration_ms": 0.175
  }
}
```
