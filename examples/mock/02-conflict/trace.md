# 执行记录：报销材料应在多少天内提交？

- 模式：`offline_mock`
- 模型/替身：`offline-observation-mock-v1`
- 状态：`needs_clarification`
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

返回摘要：读到 D02 (2026-09-01) 的 1 个原文片段。

> [D02/C01] 报销材料应在费用发生后 15 天内提交。

后续动作：`search_documents`

## 记录 4

动作：`search_documents`；已执行：`True`

公开依据：读到不同政策表述，补查适用范围和优先级依据。

参数：

```json
{
  "query": "费用报销管理办法 费用报销补充通知 适用范围 优先级",
  "limit": 5,
  "reason": "读到不同政策表述，补查适用范围和优先级依据。"
}
```

返回摘要：命中 2 份；返回 ['D01', 'D02']；has_more=False

后续动作：`finish`

## 记录 5

动作：`finish`；已执行：`True`

公开依据：查证后仍缺少消解冲突的依据，列出各方原文并请求确认。

参数：

```json
{
  "status": "needs_clarification",
  "citations": [
    {
      "document_id": "D01",
      "chunk_id": "C01",
      "quote": "报销材料应在费用发生后 30 天内提交。"
    },
    {
      "document_id": "D02",
      "chunk_id": "C01",
      "quote": "报销材料应在费用发生后 15 天内提交。"
    }
  ],
  "gaps": [
    "同一主题存在不同原文表述，资料未注明优先级或替代关系。",
    "需要确认适用范围（当前标注：未注明）。"
  ],
  "follow_up_question": "请确认适用部门及应以哪份制度为准，或补充明确的优先级/废止说明。",
  "reason": "查证后仍缺少消解冲突的依据，列出各方原文并请求确认。"
}
```

返回摘要：最终状态 needs_clarification；有效引用 2 个。

后续：结束，状态 `needs_clarification`。

## 实际输出

```json
{
  "status": "needs_clarification",
  "answer": "同主题资料表述不一致，需确认适用范围或优先级。\n- [D01/C01，2026-01-15] 报销材料应在费用发生后 30 天内提交。\n- [D02/C01，2026-09-01] 报销材料应在费用发生后 15 天内提交。",
  "citations": [
    {
      "document_id": "D01",
      "title": "费用报销管理办法",
      "version_date": "2026-01-15",
      "scope": "未注明",
      "chunk_id": "C01",
      "policy_key": "expense_submission_deadline",
      "quote": "报销材料应在费用发生后 30 天内提交。"
    },
    {
      "document_id": "D02",
      "title": "费用报销补充通知",
      "version_date": "2026-09-01",
      "scope": "未注明",
      "chunk_id": "C01",
      "policy_key": "expense_submission_deadline",
      "quote": "报销材料应在费用发生后 15 天内提交。"
    }
  ],
  "conflicts": [
    {
      "policy_key": "expense_submission_deadline",
      "scope": "未注明",
      "variants": [
        {
          "document_id": "D01",
          "version_date": "2026-01-15",
          "chunk_id": "C01",
          "quote": "报销材料应在费用发生后 30 天内提交。"
        },
        {
          "document_id": "D02",
          "version_date": "2026-09-01",
          "chunk_id": "C01",
          "quote": "报销材料应在费用发生后 15 天内提交。"
        }
      ]
    }
  ],
  "gaps": [
    "同一主题存在不同原文表述，资料未注明优先级或替代关系。",
    "需要确认适用范围（当前标注：未注明）。"
  ],
  "follow_up_question": "请确认适用部门及应以哪份制度为准，或补充明确的优先级/废止说明。",
  "stop_reason": "查证后仍缺少消解冲突的依据，列出各方原文并请求确认。",
  "question": "报销材料应在多少天内提交？",
  "run": {
    "run_id": "4fd6f784-e363-4fcb-9bba-aca7037f752b",
    "execution_mode": "offline_mock",
    "model": "offline-observation-mock-v1",
    "mock_boundary": "仅验证流程，不能证明真实模型的 ReAct 决策效果。",
    "corpus_version": "synthetic-2026-10-28-v1",
    "corpus_sha256": "b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66",
    "model_calls": 5,
    "tool_calls": 5,
    "max_steps": 14,
    "max_tool_calls": 12,
    "started_at": "2026-10-28T13:15:46.726+00:00",
    "finished_at": "2026-10-28T13:15:46.726+00:00",
    "duration_ms": 0.295
  }
}
```
