# 执行记录：报销材料应在多少天内提交？

- 模式：`offline_mock`
- 模型/替身：`offline-observation-mock-v1`
- 状态：`answered`
- 知识库 SHA256：`ea3b9afcceb42d6a5027513fe4c626526a4a013fe6b85f04bc037750618e9d4c`

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

返回摘要：读到 D02 (2026-09-01) 的 1 个原文片段。

> [D02/C01] 报销材料应在费用发生后 30 天内提交。

后续动作：`finish`

## 记录 4

动作：`finish`；已执行：`True`

公开依据：已读取相关原文，未发现同主题同范围的不同表述，引用原文作答。

参数：

```json
{
  "status": "answered",
  "citations": [
    {
      "document_id": "D01",
      "chunk_id": "C01",
      "quote": "报销材料应在费用发生后 30 天内提交。"
    }
  ],
  "gaps": [],
  "follow_up_question": "",
  "reason": "已读取相关原文，未发现同主题同范围的不同表述，引用原文作答。"
}
```

返回摘要：最终状态 answered；有效引用 1 个。

后续：结束，状态 `answered`。

## 实际输出

```json
{
  "status": "answered",
  "answer": "根据已读取的资料：\n- [D01/C01，2026-01-15] 报销材料应在费用发生后 30 天内提交。",
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
  "gaps": [],
  "follow_up_question": "",
  "stop_reason": "已读取相关原文，未发现同主题同范围的不同表述，引用原文作答。",
  "question": "报销材料应在多少天内提交？",
  "run": {
    "run_id": "c19fe3d9-6b1a-4b96-aa6b-9a5b2d12c66c",
    "execution_mode": "offline_mock",
    "model": "offline-observation-mock-v1",
    "mock_boundary": "仅验证流程，不能证明真实模型的 ReAct 决策效果。",
    "corpus_version": "synthetic-2026-10-28-v1:11-conflict-removed",
    "corpus_sha256": "ea3b9afcceb42d6a5027513fe4c626526a4a013fe6b85f04bc037750618e9d4c",
    "model_calls": 4,
    "tool_calls": 4,
    "max_steps": 14,
    "max_tool_calls": 12,
    "started_at": "2026-10-28T13:15:46.734+00:00",
    "finished_at": "2026-10-28T13:15:46.734+00:00",
    "duration_ms": 0.212
  }
}
```
