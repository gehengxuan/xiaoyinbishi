# 04 · 项目贡献、AI 协作与验证记录

## 我的交付角色

我借助 Codex 完成第 3 题企业知识问答 Agent，并选择 DeepSeek 作为运行时模型。我的交付目标是把题目中的“可靠回答”落成可运行、可复现、能追踪决策的项目：回答要有原文，冲突要能说明，资料不足或工具失败要有明确状态，模型不能无限调用工具。

我将项目按需求、实现、真实验证和复盘组织成完整交付，并用源码、反例和实际 Trace 说明技术取舍。选题、DeepSeek 模型和完整交付目标由我确认；需求细化、方案推导、代码、测试及文档的具体产出使用了 Codex 辅助。下面呈现的是这份 AI 辅助项目形成的工程选择及其验证结果。

## 项目中体现的判断与工程能力

下表记录本项目在 AI 辅助下形成并落地的方案选择；不将这些内容表述为独立手写或未经辅助的设计。

| 要解决的问题 | 本项目的选择及原因 | 可核对证据 |
|---|---|---|
| 员工需要能够据以行动的制度依据 | 将可靠性拆成原文支持、范围/冲突确认、明确任务状态；资料不足时保留问题，避免擅自给出唯一结论 | [需求与验收](01-requirements.md)、[真实冲突记录](../examples/live/02-conflict/trace.md) |
| 模型需要根据观察改变动作 | 保留检索、读取、结束三个模型可选动作；工具结果回传模型，运行时只执行、校验和限制预算 | [Agent 循环](../src/knowledge_agent/agent.py)、[失败后改写查询](../examples/live/06-transient-tool-failure/trace.md) |
| “有引用”仍可能搭配编造结论 | 模型选择证据，程序核对本次已读原文并渲染事实答案；同时承认精确引用不能保证语义相关性 | [引用校验](../src/knowledge_agent/agent.py)、[负例测试](../tests/test_guardrails.py) |
| 只看一个命中可能漏掉冲突 | 关联同主题同范围的候选文档，要求补读；版本日期仅为来源信息，不自动代表优先级 | [资料工具](../src/knowledge_agent/knowledge.py)、[D01/D02 真实路径](../examples/live/02-conflict/trace.md) |
| 模型/工具异常不能让状态失真 | 保存已成功步骤的证据，明确工具失败与执行上限；不把 Mock 结果冒充真实模型结果 | [持续失败](../examples/live/07-persistent-tool-failure/trace.md)、[达到上限](../examples/live/09-step-limit/trace.md) |
| 测试通过是否只是因为答案写死 | 修改年假天数、消除文档冲突，检查答案与后续动作是否随资料改变 | [10 → 12 天](../examples/live/10-document-mutation/trace.md)、[冲突消除](../examples/live/11-conflict-removed/trace.md) |
| 评估脚本也可能判断错误 | 保留首轮 10/11，修正等价引用集合的过窄断言；用原始记录重评，保持输入、输出与 Trace 不变 | [首轮结果](../examples/live-initial/summary.md)、[重评说明](../examples/live/review.md)、[评估回归测试](../tests/test_evaluation.py) |

这些内容展示项目如何把业务边界转成工程约束，并用反例检验约束。原生 Python、CLI 和小型本地知识库服务于本题的时间与验收范围；语义召回、生产权限和长期状态管理列入后续工作。

## AI 实际使用范围

**Codex** 参与了需求拆解、方案分析、提示词、合成资料、代码实现、自动测试、API 接入、实际命令执行、Trace 整理和文档修改。具体代码生成、联调排查、测试执行、评估断言修正与 Git 推送由 Codex 借助工具完成。该项目按 AI 辅助开发提交，不声称所有代码由本人独立手写，也不把工具执行记作本人独立复测。

**DeepSeek** 是应用运行时的决策模型。2026-10-29 实际执行了 11 条问题，选择工具、观察返回并决定下一步；最终事实文本由程序从模型选定且通过校验的原文渲染。`examples/live-initial/` 保存首次实际运行，`examples/live/` 保存同一批原始记录的重评副本。

**离线替身** 包括 `OfflineMockModel`、测试中的 `ScriptedModel` 与本机假 HTTP 服务。它们分别验证流程、运行时约束和接口序列化，不作为真实模型决策效果证据。

供应商接入参考：[DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)、[Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)；可选 OpenAI 入口参考[官方 Function Calling](https://developers.openai.com/api/docs/guides/function-calling)。

## 验证与改进结果

- 45 项自动测试通过，覆盖业务路径、引用篡改、遗漏冲突、历史误导、工具错误和执行上限：[原始日志](../examples/test-results.txt)。
- 11 条离线用例通过，明确限定为流程验证：[离线汇总](../examples/mock/summary.md)。
- 11 条真实 DeepSeek 问题完成，覆盖题目六项验收与额外回归；首轮 10/11，修正评估断言后对原始记录重评 11/11：[真实复核](../examples/live/review.md)。
- 真实运行保留了证书/余额预检失败，以及 5 次协议响应错误后的恢复。未将失败步骤改写为成功，也未把不完整 token 记录表述为完整成本。

## 用时与后续边界

[work-log.json](work-log.json) 记录两个开发与验证协作时段，合计约 62.46 分钟，未把隔夜间隔计入。该口径是有时间戳的阶段跨度，不等同于本人纯编码工时；未记录的额外复习或修改时间不作估算。

本次已完成核心链路、真实验收及 GitHub 交付。后续优先验证未见问题、范围判断与多次运行稳定性，并补全协议错误响应的安全审计信息。密钥仅存于本机配置，不进入仓库。
