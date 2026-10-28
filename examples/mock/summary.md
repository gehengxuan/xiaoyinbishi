# 实际验收结果

模式：`mock`；通过：11/11。

离线流程验收；真实模型效果尚未验证。

| 用例 | 状态 | 检查 | 实际动作 | 记录 |
|---|---|---|---|---|
| 01-clear | answered | PASS | search_documents → read_document → finish | [Trace](01-clear/trace.md) |
| 02-conflict | needs_clarification | PASS | search_documents → read_document → read_document → search_documents → finish | [Trace](02-conflict/trace.md) |
| 03-out-of-domain | not_found | PASS | search_documents → search_documents → finish | [Trace](03-out-of-domain/trace.md) |
| 04-paraphrase | answered | PASS | search_documents → read_document → finish | [Trace](04-paraphrase/trace.md) |
| 05-context-follow-up | answered | PASS | search_documents → read_document → finish | [Trace](05-context-follow-up/trace.md) |
| 06-transient-tool-failure | answered | PASS | search_documents → search_documents → read_document → finish | [Trace](06-transient-tool-failure/trace.md) |
| 07-persistent-tool-failure | tool_error | PASS | search_documents → read_document → read_document → read_document → finish | [Trace](07-persistent-tool-failure/trace.md) |
| 08-missing-topic | needs_clarification | PASS | finish | [Trace](08-missing-topic/trace.md) |
| 09-step-limit | limit_reached | PASS | search_documents | [Trace](09-step-limit/trace.md) |
| 10-document-mutation | answered | PASS | search_documents → read_document → finish | [Trace](10-document-mutation/trace.md) |
| 11-conflict-removed | answered | PASS | search_documents → read_document → read_document → finish | [Trace](11-conflict-removed/trace.md) |
