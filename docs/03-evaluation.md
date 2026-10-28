# 03 · 验证、实际结果与限制

## 证据分层

当前已执行的验收模式是 **offline_mock**。11/11 用例通过的是流程和输出契约检查，不是 LLM 决策正确率。真实 DeepSeek API 尚未运行；不存在真实模型通过率、成本或稳定性结论。本机假 HTTP 服务仅用于测试消息序列化与观察回传，不属于真实模型验证。

实际可执行测试输出：[test-results.txt](../examples/test-results.txt)、[机器摘要](../examples/test-results.json)。测试覆盖业务路径、篡改引用、遗漏冲突文档、模型协议错误、上限、配置以及 HTTP 请求格式。数量、耗时和 Python 版本以机器摘要为准。

复现：

```bash
PYTHONPATH=src python3 scripts/test.py
PYTHONPATH=src python3 scripts/evaluate.py --provider mock
```

## 用例预期与实际结果

每个链接目录同时保存 `input.json`、`output.json`、`trace.json`、`trace.md`、`run-config.json`、`checks.json`；变更资料的用例额外保存 `corpus.json`。汇总：[summary.md](../examples/mock/summary.md)、[evaluation.json](../examples/mock/evaluation.json)。

| 用例与验收点 | 预期 | 实际离线结果与记录 |
|---|---|---|
| 明确答案 | D03 原文、10 天、answered | [01-clear](../examples/mock/01-clear/trace.md)，符合 |
| 文档冲突 | 30/15 天双方引用、追问适用制度 | [02-conflict](../examples/mock/02-conflict/trace.md)，needs_clarification |
| 资料外问题 | 查询改写后仍无资料，不编写政策 | [03-out-of-domain](../examples/mock/03-out-of-domain/trace.md)，not_found |
| 相似问题 | 口语表达命中同一证据 | [04-paraphrase](../examples/mock/04-paraphrase/trace.md)，answered、D03/C01 |
| 上下文追问 | 理解“那”指年假，重新读取申请规则 | [05-context-follow-up](../examples/mock/05-context-follow-up/trace.md)，answered、提前 3 个工作日 |
| 一次工具失败 | 观察错误后选择再试，失败有记录 | [06-transient-tool-failure](../examples/mock/06-transient-tool-failure/trace.md)，answered |
| 持续工具失败 | D01 成功保留，D02 失败不能冒充成功 | [07-persistent-tool-failure](../examples/mock/07-persistent-tool-failure/trace.md)，tool_error，仅 D01 为部分证据 |
| 信息不足 | 缺主题时具体追问 | [08-missing-topic](../examples/mock/08-missing-topic/trace.md)，needs_clarification |
| 上限 | 只允许 1 轮决策，不能称已回答 | [09-step-limit](../examples/mock/09-step-limit/trace.md)，limit_reached |
| 文档变更 | D03 的 10 天改为 12 天，不能仍答 10 天 | [10-document-mutation](../examples/mock/10-document-mutation/trace.md)，answered、12 天 |
| 冲突消除 | D02 改为同样 30 天后动作改变 | [11-conflict-removed](../examples/mock/11-conflict-removed/trace.md)，answered，不再补查优先级和追问 |

自动验收检查状态、预期引用文档集合、关键原文、冲突组数、真实故障次数、实际成功读取与引用一致性、调用上限，以及未完成状态的资料缺口。预期值只供评估脚本断言，不进入模型消息。

## 反例与失败处理验证

- 引用不存在或未读取的文档：返回 `UNREAD_CITATION`，模型有机会补读。
- 已读原文写 10 天，提交引用却改成 100 天：返回 `INVALID_QUOTE`，不会输出伪造事实。
- 只读取 D01 就尝试回答：返回 `EVIDENCE_INCOMPLETE`；读取 D02 后按新版日期选择 15 天：返回 `UNRESOLVED_CONFLICT`。
- 冲突澄清只引用一方：返回 `CONFLICT_CITATIONS_REQUIRED`。
- 传入额外自由事实答案字段、未知工具、错误参数：拒绝，并计入调用预算。
- 历史故意写错“99 天、提前 1 分钟”：单测仍要求重新读取当前 D03，引用 3 个工作日。
- 模型网络失败：返回 `model_error`，保留已读证据，不切换 Mock。工具错误的恢复动作由模型/替身下一轮选择，不在执行器中自动重试。

这些是受控负例的预期拒绝，不代表真实模型遇到负例一定会选择正确恢复路径。

## 尚未完成与已知限制

1. **真实模型效果未验证**：缺少可用本地 DeepSeek 密钥。代码与协议测试不能代替至少两条真实模型动作路径。提交前应运行完整真实验收，并将真实结果、失败与人工检查写回本文件。
2. **只保证引用一致性，不保证语义选材正确**：错误主题的真实原文仍可能被模型选中，自动验收不能覆盖所有语义错误。短片段摘录也不能表达跨文档复杂推理。
3. **冲突检测依赖人工元数据**：同范围同键的文字差异会保守阻断；跨键、范围标注错误、适用关系变化及措辞等价均需更强判断。当前版本没有可执行的权威优先级消解规则，因此冲突保留给用户确认。
4. **召回有限**：有限同义词与双字重叠不适合大知识库；没有向量召回、重排或全库完整性证明。`related_document_ids` 只覆盖当前人工标注的关联资料。
5. **小样本**：11 条合成问题、一次确定性离线运行，不能证明跨领域能力或随机稳定性。CI 配置支持 Python 3.11/3.13，但本机实际执行版本以日志为准，未声称 GitHub CI 已运行。
6. 未推送指定 GitHub 远端；候选人个人实际手工用时、独立修改与验证记录仍需本人补充。

## 补齐真实模型证据

```bash
PYTHONPATH=src python3 scripts/evaluate.py --provider deepseek --env-file .env
```

运行后检查 `examples/live/summary.md` 和每条原始 Trace。至少人工核对：答案是否对题，引用是否足够，冲突双方是否都读到，日期是否被擅自当作优先级，无资料时是否改写/追问，以及失败后的状态是否真实。自动检查失败应如实保留，不覆盖为“通过”。真实运行记录应与 Mock 分别保存。
