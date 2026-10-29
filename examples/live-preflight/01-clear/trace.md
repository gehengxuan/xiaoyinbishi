# 执行记录：正式员工一年有多少天带薪年假？

- 模式：`live_model`
- 模型/替身：`deepseek:deepseek-flash`
- 状态：`model_error`
- 知识库 SHA256：`b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66`

## 记录 1

事件：`model_error`

返回摘要：模型 API 网络错误或超时；未自动重试，也未切换为 Mock。

后续：结束，状态 `model_error`。

## 实际输出

```json
{
  "status": "model_error",
  "answer": "任务未完成；已获取的资料保留在 citations，不能据此视为已回答。",
  "citations": [],
  "conflicts": [],
  "gaps": [
    "模型 API 网络错误或超时；未自动重试，也未切换为 Mock。"
  ],
  "follow_up_question": "",
  "stop_reason": "模型 API 网络错误或超时；未自动重试，也未切换为 Mock。",
  "question": "正式员工一年有多少天带薪年假？",
  "run": {
    "run_id": "cca1730a-113c-41d5-97fa-8dc290ae54a1",
    "execution_mode": "live_model",
    "model": "deepseek:deepseek-flash",
    "mock_boundary": null,
    "corpus_version": "synthetic-2026-10-28-v1",
    "corpus_sha256": "b4fcde35c2a33ffc2c60ea3c5e08c4fbabe665b386af08d1ca009707ab9cee66",
    "model_calls": 1,
    "tool_calls": 0,
    "max_steps": 14,
    "max_tool_calls": 12,
    "started_at": "2026-10-29T05:20:08.976+00:00",
    "finished_at": "2026-10-29T05:20:09.029+00:00",
    "duration_ms": 53.308
  }
}
```
