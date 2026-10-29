# DeepSeek 真实运行复核

复核者：Codex；复核日期：2026-10-29（Asia/Shanghai）。这是 AI 对原始执行记录的复核，未声称候选人本人已独立复测。

## 证据来源与评分变化

供应商实际返回的模型名为 `deepseek-flash`。11 条问题共 40 次模型请求，其中 35 个动作被解析、带真实 response ID；5 个响应未满足单动作协议，运行时反馈后恢复。完整原始记录见 [live-initial](../live-initial/summary.md)。

首轮 10/11。唯一失败是第 11 例的旧断言只接受 D01，但用例已经把 D02 改成与 D01 完全相同的 30 天；模型引用两方仍然有原文支持。修正断言允许 D01、D02 或两者，其他事实/状态/原文检查不变。原始旧断言快照：[cases.json](../live-initial/cases.json)。

本目录为**对同一批原始记录的重评，11/11**。`input.json`、`output.json`、`trace.json`、`trace.md`、`run-config.json` 和资料快照与首轮逐字一致；仅 checks 与汇总重新生成。没有为了取得特定答案重新调用模型，没有改写模型 Trace。

## 逐条复核

| 用例 | 状态 | 事实与动作检查 |
|---|---|---|
| [01 正常](01-clear/trace.md) | answered | 查询正式员工年假 → 读取 D03 → 引用 C01 的 10 天。ID、版本和原文一致。 |
| [02 冲突](02-conflict/trace.md) | needs_clarification | 读到 D01=30 天、D02=15 天；范围均未注明，未把新日期视为优先级，引用双方并追问适用制度。一次协议错误后恢复。 |
| [03 资料外](03-out-of-domain/trace.md) | not_found | 从“火星移民补贴”改写为“移民 安家 补贴 福利政策”，两次无命中后停止，没有编写公司补贴政策。 |
| [04 改写问题](04-paraphrase/trace.md) | answered | 仍依据 D03 的 10 天作答。额外附带了提前 3 个工作日申请的真实原文，相关但超出提问，可进一步收紧选材。 |
| [05 上下文](05-context-follow-up/trace.md) | answered | 使用历史定位年假，重新读取 D03/C02，正确回答提前 3 个工作日。 |
| [06 单次故障](06-transient-tool-failure/trace.md) | answered | 第一次搜索失败；模型观察后改写查询，再读 D03 并结束。不是执行器自动重试。 |
| [07 持续故障](07-persistent-tool-failure/trace.md) | tool_error | D01 成功，D02 三次读取失败；保留 D01，并明确不能排除未读资料的冲突。两次协议错误后恢复。 |
| [08 缺主题](08-missing-topic/trace.md) | needs_clarification | 未凭空假设“那个”的主题，提出具体追问。 |
| [09 上限](09-step-limit/trace.md) | limit_reached | 完成一次搜索就耗尽允许步数，状态明确未完成。 |
| [10 改数值](10-document-mutation/trace.md) | answered | 从 10 天的基准答案变为新原文的 12 天，没有沿用旧答案。 |
| [11 消除冲突](11-conflict-removed/trace.md) | answered | 读取两份资料，均为 30 天，选择结束而不是冲突追问。两次协议错误后恢复；引用两方均正确。 |

## 两条主要模型动作路径

正常路径：`search_documents → read_document(D03) → finish(answered)`。

冲突路径：`search_documents → 协议错误反馈 → read_document(D01) → read_document(D02) → finish(needs_clarification)`。模型根据新读到的不同期限和缺少优先级依据选择追问，而非按新版日期直接给出 15 天。

工具错误路径另外显示，模型可改写搜索重试，也可在持续错误时保留成功证据并停止。真实冲突路径未额外搜索优先级说明；已通过读取双方资料核实范围和差异，不能把离线替身额外搜索的路径描述成真实模型路径。

## 审计限制

- 5 次协议错误响应没有持久化原始正文、response ID 和 token 用量，因此只能确认“不满足单动作协议”，不推断具体格式原因。
- 已保存的 35 个动作响应报告 token 用量合计 51,975，排除了协议错误响应，不能当作完整账单或费用。
- 一轮合成小样本仍有覆盖偏差；精确引用不保证任何新问题上的相关性、召回和范围判断都正确。
- 两次连接/余额预检失败保存在 [live-preflight](../live-preflight/summary.md)、[live-preflight-ca](../live-preflight-ca/summary.md)，它们没有获得模型决策，不算作通过路径。
