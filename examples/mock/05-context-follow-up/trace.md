# 执行记录：那需要提前多久申请？

- 模式：`offline_mock`
- 模型/替身：`offline-observation-mock-v1`
- 状态：`answered`
- 知识库 SHA256：`b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66`

> 仅验证流程，不能证明真实模型的 ReAct 决策效果。

## 记录 1

动作：`search_documents`；已执行：`True`

公开依据：先检索与问题及对话上下文有关的文档。

参数：

```json
{
  "query": "正式员工一年有多少天年假？ 那需要提前多久申请？",
  "limit": 5,
  "reason": "先检索与问题及对话上下文有关的文档。"
}
```

返回摘要：命中 1 份；返回 ['D03']；has_more=False

后续动作：`read_document`

## 记录 2

动作：`read_document`；已执行：`True`

公开依据：命中资料只是线索，需要读取原文及同主题候选文档。

参数：

```json
{
  "document_id": "D03",
  "reason": "命中资料只是线索，需要读取原文及同主题候选文档。"
}
```

返回摘要：读到 D03 (2026-06-01) 的 2 个原文片段。

> [D03/C01] 正式员工每年享有 10 天带薪年假。

> [D03/C02] 年假须至少提前 3 个工作日申请。

后续动作：`finish`

## 记录 3

动作：`finish`；已执行：`True`

公开依据：已读取相关原文，未发现同主题同范围的不同表述，引用原文作答。

参数：

```json
{
  "status": "answered",
  "citations": [
    {
      "document_id": "D03",
      "chunk_id": "C02",
      "quote": "年假须至少提前 3 个工作日申请。"
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
  "answer": "根据已读取的资料：\n- [D03/C02，2026-06-01] 年假须至少提前 3 个工作日申请。",
  "citations": [
    {
      "document_id": "D03",
      "title": "员工休假制度",
      "version_date": "2026-06-01",
      "scope": "正式员工",
      "chunk_id": "C02",
      "policy_key": "annual_leave_notice",
      "quote": "年假须至少提前 3 个工作日申请。"
    }
  ],
  "conflicts": [],
  "gaps": [],
  "follow_up_question": "",
  "stop_reason": "已读取相关原文，未发现同主题同范围的不同表述，引用原文作答。",
  "question": "那需要提前多久申请？",
  "run": {
    "run_id": "534ddf61-d899-49fa-be14-ad0441cce46b",
    "execution_mode": "offline_mock",
    "model": "offline-observation-mock-v1",
    "mock_boundary": "仅验证流程，不能证明真实模型的 ReAct 决策效果。",
    "corpus_version": "synthetic-2026-10-28-v1",
    "corpus_sha256": "b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66",
    "model_calls": 3,
    "tool_calls": 3,
    "max_steps": 14,
    "max_tool_calls": 12,
    "started_at": "2026-10-28T13:15:46.729+00:00",
    "finished_at": "2026-10-28T13:15:46.729+00:00",
    "duration_ms": 0.145
  }
}
```
