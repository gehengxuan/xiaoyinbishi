# 03 · 验证、实际结果与限制

## 证据分层

当前已完成 **offline_mock** 与 **DeepSeek 真实 API** 两类记录。离线 11/11 只验证流程；2026-10-29 的真实运行使用 `deepseek-flash`，首轮断言 10/11，修正一条过窄的引用集合断言后，对同一批原始记录重评 11/11。这是单次小型合成集结果，不能当作广泛的模型决策正确率或稳定性结论。本机假 HTTP 服务仍只属于接口测试。

实际可执行测试输出：[test-results.txt](../examples/test-results.txt)、[机器摘要](../examples/test-results.json)，当前 **45 项通过**。测试覆盖业务路径、篡改引用、遗漏冲突文档、模型协议错误、上限、配置、HTTP 请求格式、余额/TLS 诊断与无网络重评。

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

## 真实模型运行与逐条复核

真实记录：[汇总](../examples/live/summary.md)、[逐条复核](../examples/live/review.md)、[机器检查结果](../examples/live/evaluation.json)。首轮原始记录及旧断言结果完整保存在 [live-initial](../examples/live-initial/summary.md)。

| 用例 | 真实结果 | 模型请求数 | 核对结论 |
|---|---|---:|---|
| 01 明确答案 | answered | 3 | D03/C01，10 天，原文与版本正确 |
| 02 冲突 | needs_clarification | 5 | 读取 D01/D02，列出 30/15 天；未按新日期擅自选择 |
| 03 资料外 | not_found | 3 | 两次不同查询均无命中，不编写补贴政策 |
| 04 改写问题 | answered | 3 | D03 的 10 天正确；额外引用申请提前期，信息真实但可更简洁 |
| 05 上下文 | answered | 3 | 重新读取 D03/C02，提前 3 个工作日 |
| 06 单次故障 | answered | 4 | 观察失败后模型改写查询再试，成功后读取原文 |
| 07 持续故障 | tool_error | 8 | D02 三次读取失败，保留 D01，未把部分证据当作唯一答案 |
| 08 缺主题 | needs_clarification | 1 | 直接提出具体澄清问题 |
| 09 上限 | limit_reached | 1 | 搜索后耗尽预算，明确未完成 |
| 10 文档变更 | answered | 3 | 答案从 10 天变为 12 天 |
| 11 冲突消除 | answered | 6 | 两份原文均为 30 天，不再请求冲突确认 |

主验收共 40 次模型请求，35 个已解析动作带供应商 response ID；另有 5 个响应未满足单动作协议，分别出现在 02/07/11，模型根据运行时反馈恢复。协议错误的原始响应正文未持久化，因此不进一步推断具体格式原因。已保存的 35 个动作响应共报告 51,975 tokens；该数**不含 5 个协议错误响应**，不能作为完整用量或账单金额。

真实冲突路径没有额外搜索优先级文档，而是读取两份原文及其范围信息后请求澄清；它与离线替身的固定策略不同。正常、无资料、冲突及错误恢复路径均由真实模型根据当轮观察选择。

### 首轮 10/11 与重评 11/11 的差异

首轮仅 `11-conflict-removed` 的“引用文档集合”断言失败：旧用例只允许 D01，但 D02 已被用例修改成同样的 30 天，模型引用 D01 和 D02 都有原文支持。答案、状态、原文一致性和冲突组数原本都通过。

修正仅扩展该例允许的集合为 `{D01}`、`{D02}` 或 `{D01,D02}`，继续拒绝空集合及其他文档；未改动模型、提示词、原始输出或 Trace。[旧用例快照](../examples/live-initial/cases.json)、旧 checks 和 10/11 汇总均保留。重评将原始记录逐字复制到 `examples/live/`，只重新生成检查结果与汇总，不调用 API。

```bash
PYTHONPATH=src python3 scripts/evaluate.py --provider deepseek \
  --recheck-from examples/live-initial --output-dir runs/recheck
```

### 两次真实预检失败

首先出现 Python 默认 CA 路径缺失，记录见 [live-preflight](../examples/live-preflight/01-clear/trace.md)。用 `SSL_CERT_FILE=/etc/ssl/cert.pem` 保持证书校验后连接成功，但供应商返回 HTTP 402，记录见 [live-preflight-ca](../examples/live-preflight-ca/01-clear/trace.md)；[官方错误码](https://api-docs.deepseek.com/zh-cn/quick_start/error_codes/)将 402 定义为余额不足。用户处理余额后才进行上述完整运行。这两条预检没有获得模型决策，不计入主验收通过率。

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

1. **单轮真实小样本**：已完成真实 API 验收与 Codex 对记录的逐条复核，没有多随机种子或未见集稳定性结果。45 项单测与 11 条用例不能证明开放域质量。
2. **只保证引用一致性，不保证语义选材正确**：错误主题的真实原文仍可能被模型选中，自动验收不能覆盖所有语义错误。短片段摘录也不能表达跨文档复杂推理。
3. **冲突检测依赖人工元数据**：同范围同键的文字差异会保守阻断；跨键、范围标注错误、适用关系变化及措辞等价均需更强判断。当前版本没有可执行的权威优先级消解规则，因此冲突保留给用户确认。
4. **召回有限**：有限同义词与双字重叠不适合大知识库；没有向量召回、重排或全库完整性证明。`related_document_ids` 只覆盖当前人工标注的关联资料。
5. **协议与审计范围**：模型偶尔返回未满足单动作要求的响应，虽然本轮恢复成功，仍会消耗步骤预算；该类响应的 ID 与用量没有被当前适配器保留。CI 配置支持 Python 3.11/3.13，但本机版本以日志为准，未声称 GitHub CI 已运行。
6. 已推送到 [GitHub main 分支](https://github.com/gehengxuan/xiaoyinbishi/tree/main)；远端 CI 结果尚未单独核验，本机验证环境及执行结果以保存的日志为准。

## 复现新的真实运行

```bash
SSL_CERT_FILE=/etc/ssl/cert.pem PYTHONPATH=src python3 scripts/evaluate.py \
  --provider deepseek --env-file .env --output-dir examples/live-new
```

`SSL_CERT_FILE` 仅为本次 macOS Python 的证书配置，其他平台按自身可信 CA 配置，默认验证正常时可省略。新运行使用新目录保留既有证据，并再次核对语义相关性、范围与失败处理；自动断言不能替代这些检查。
