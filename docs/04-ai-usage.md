# 04 · AI 使用范围与贡献记录

## 实际协作方式

本项目允许 AI 辅助。以下记录当前可核对的实际工作，不能把 AI 生成的代码和文档包装为候选人独立完成。

| 参与方 | 已发生的工作 |
|---|---|
| 用户/候选人 | 提供完整笔试要求；确认实现第 3 题与 DeepSeek；在本机配置 API 密钥，处理 API 余额；指定 GitHub 仓库并授权推送 main |
| Codex（本对话） | 需求拆解、代码实现、合成资料、工具与提示词、引用校验、测试、运行脚本、实际离线运行与结果记录、文档及提交说明 |
| DeepSeek | 2026-10-29 实际运行 11 条问题，真实选择工具、观察反馈并结束；记录位于 `examples/live-initial/` 与原样复制重评的 `examples/live/` |

没有记录到候选人本人手写代码、独立测试或修改结果。若之后由候选人调整检索、提示词或规则，应在此补充实际改动、原因、文件/commit 与运行结果。不要用“我独立完成所有代码”等未发生的表述。

## 关键指令与修改

- 初始目标：按题目 3 准备可运行代码、测试和全部交付文档。
- 用户确定模型供应商后，从通用兼容接口补充专用 DeepSeek 适配：使用非思考模式、`max_tokens`、标准端点，移除仅 Beta 支持的 strict 参数；运行时继续严格校验引用与参数。
- 为防止真实引用旁边出现编造结论，采用提取式事实答案：模型选择证据，程序校验并渲染完整短原文。
- 为防止 top-1 隐藏冲突，搜索元数据显式带同主题、同范围的关联文档，回答校验要求补读。
- 检索增加同义词扩展与最低得分阈值，降低“公司”等泛词正文命中带来的噪声。
- 真实联调遇到证书与 HTTP 402 后，保留失败记录，使用受信系统 CA 继续验证，并添加不暴露密钥的错误诊断及测试。
- 首轮真实验收 10/11；发现“相同原文只能引 D01”的断言过窄，扩展为允许 D01、D02 或两者，在不改写原始 Trace 的情况下重评为 11/11。

以上实现与修改均由 Codex 完成，不记作候选人个人手工贡献。官方协议核对来源：[DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)、[DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)、[OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling)。

## 已实际验证

Codex 在本地运行并保存了：

- [自动测试原始输出](../examples/test-results.txt)与[机器摘要](../examples/test-results.json)。
- [11 条离线输入、实际输出和动作记录](../examples/mock/summary.md)。
- [11 条真实 DeepSeek 记录与逐条复核](../examples/live/review.md)，45 项本地测试通过。
- 正常/冲突/无资料/上下文/失败场景，以及变更文档后答案与结束动作变化。

测试中的 `ScriptedModel` 和本机假 HTTP 服务是受控测试替身；`OfflineMockModel` 是确定性规则。它们都不是 DeepSeek 真实模型。没有把预设的动作序列或伪造模型日志当作真实模型运行提交。

真实记录确实来自 DeepSeek API，但对话提示词、工具与资料由本项目设计，最终事实文本由校验通过的模型选定原文渲染。不能将输出全部描述为候选人手写或不受约束的模型自由生成。

## 时间与未完成事项

可核对的 AI 协作开发时段记录在 [work-log.json](work-log.json)，使用 UTC 时间戳和 Asia/Shanghai 显示时间。它是本次 AI 协作的墙钟跨度，不是候选人本人实际劳动时间；候选人手工用时尚未提供。

真实模型 API 验证与 GitHub main 分支推送已完成，推送命令由 Codex 执行。候选人亲自理解/修改/复测的记录仍需补齐。候选人已实际完成密钥与余额配置，其手工时间未提供。模型账户密钥仅保存在本机 `.env` 或环境变量中，不能提交。
