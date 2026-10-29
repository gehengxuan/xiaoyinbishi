# 企业知识问答 Agent · 小影校招项目题 3

面向查询制度或产品信息的员工，交付能核对依据的回答，并在冲突、资料不足和工具失败时给出明确状态。项目采用 Python CLI，模型选择检索或读取工具，观察实际返回后继续查证、追问或结束。

**交付状态：45 项测试通过；11 条 DeepSeek 真实用例完成。首轮断言 10/11，修正一条过窄的引用集合断言后，同一批原始记录重评 11/11。代码已推送到 [GitHub 仓库](https://github.com/gehengxuan/xiaoyinbishi)的 `main` 分支。** 原始失败与重评结果分别保留；这是一轮小样本验收，不代表广泛稳定性。离线 Mock 仅证明流程。

## 关键判断与工程证据

本项目按“业务边界 → 模型决策 → 工程约束 → 验证改进”组织实现。评审可以直接检查以下取舍及其结果。

| 能力 | 本项目的选择 | 证据 |
|---|---|---|
| 业务理解 | 将可靠回答落实为原文支持、冲突确认与明确的未完成状态；没有优先级依据时保留冲突 | [需求](docs/01-requirements.md)、[真实冲突路径](examples/live/02-conflict/trace.md) |
| Agent 决策 | 每轮由模型选动作，工具观察回传模型；遇到失败可改写查询，持续失败可保留证据并停止 | [运行循环](src/knowledge_agent/agent.py)、[实际错误恢复](examples/live/06-transient-tool-failure/trace.md) |
| 工程可靠性 | 校验已读原文、限制工具和步数、保留成功结果；状态与真实执行一致 | [负例测试](tests/test_guardrails.py)、[持续失败](examples/live/07-persistent-tool-failure/trace.md) |
| 效果验证 | 除正常问答外，修改文档数值与冲突内容，检查答案和下一步动作是否随证据变化 | [数值变化](examples/live/10-document-mutation/trace.md)、[冲突消除](examples/live/11-conflict-removed/trace.md) |
| 学习与改进 | 发现引用集合断言误判后保留首轮失败，用不变的原始记录重评；同时记录协议恢复和审计限制 | [首轮 10/11](examples/live-initial/summary.md)、[重评复核](examples/live/review.md) |

项目以 AI 辅助方式完成，具体参与范围、交付职责和依据见[贡献与 AI 使用记录](docs/04-ai-usage.md)；[面试讲解提纲](docs/07-interview-walkthrough.md)按源码和实际 Trace 展开上述判断。

## 评审入口

| 内容 | 入口 |
|---|---|
| 真实 DeepSeek 汇总、逐条复核与重评说明 | [examples/live/summary.md](examples/live/summary.md) · [review.md](examples/live/review.md) |
| 真实正常路径 / 冲突路径 / 失败路径 | [01-clear](examples/live/01-clear/trace.md) · [02-conflict](examples/live/02-conflict/trace.md) · [07-persistent-tool-failure](examples/live/07-persistent-tool-failure/trace.md) |
| 首轮 10/11 原始断言结果 | [examples/live-initial/summary.md](examples/live-initial/summary.md) |
| 实际离线验收结果、11 条不同输入 | [examples/mock/summary.md](examples/mock/summary.md) |
| 明确答案：检索 → 读取 → 回答 | [01-clear/trace.md](examples/mock/01-clear/trace.md) |
| 冲突：读取双方 → 补查 → 追问 | [02-conflict/trace.md](examples/mock/02-conflict/trace.md) |
| 持续失败：保留已读资料 → 未完成 | [07-persistent-tool-failure/trace.md](examples/mock/07-persistent-tool-failure/trace.md) |
| 自动化测试实际输出 | [examples/test-results.txt](examples/test-results.txt) |
| 需求 / 设计 / 评估 | [01](docs/01-requirements.md) · [02](docs/02-solution.md) · [03](docs/03-evaluation.md) |
| 项目贡献与 AI 协作 / 复盘 / 面试讲解 | [04](docs/04-ai-usage.md) · [05](docs/05-retrospective.md) · [07](docs/07-interview-walkthrough.md) |

## 环境与安装

Python **3.11 或以上**。本机验证版本及实际测试数量见 [test-results.json](examples/test-results.json)。运行与测试都只用标准库，无须安装第三方库或下载模型。以下命令均从仓库根目录执行。

```bash
python3 --version
PYTHONPATH=src python3 -m knowledge_agent --provider mock \
  --question '正式员工一年有多少天带薪年假？' \
  --output-dir runs/clear
```

`stdout` 为 JSON，Mock 提示写到 `stderr`。结果及输入、JSON Trace、可读 Trace 存入 `--output-dir`。

正常结果的核心字段如下；这段是字段示意，完整实际输出见上面的运行记录。

```json
{
  "status": "answered",
  "answer": "根据已读取的资料：\n- [D03/C01，2026-06-01] 正式员工每年享有 10 天带薪年假。",
  "citations": [{
    "document_id": "D03", "chunk_id": "C01", "version_date": "2026-06-01",
    "quote": "正式员工每年享有 10 天带薪年假。"
  }],
  "conflicts": [], "gaps": [], "follow_up_question": ""
}
```

## DeepSeek 真实模型运行

1. 复制 `.env.example` 为 `.env`，仅在本机填写 `DEEPSEEK_API_KEY`。`.env` 已被 Git 忽略，不要把密钥写进示例、Trace 或命令参数。
2. 默认 `DEEPSEEK_BASE_URL=https://api.deepseek.com`、`DEEPSEEK_MODEL=deepseek-flash`，可以在文件中修改。`--env-file` 只读取简单 `KEY=value`，不会执行 shell 代码，也不做变量展开。
3. 运行真实模型，并把记录写到独立目录。

```bash
cp .env.example .env
# 在编辑器中填写 .env；若已经配置过，请勿再次覆盖。
PYTHONPATH=src python3 -m knowledge_agent --provider deepseek --env-file .env \
  --question '报销材料应在多少天内提交？' \
  --output-dir runs/deepseek-conflict

# 重新验收：实际调用 API，使用新目录保留已提交的原始证据。
PYTHONPATH=src python3 scripts/evaluate.py --provider deepseek --env-file .env \
  --output-dir examples/live-new

# 先检查两条真实路径也可以；完整交付仍应运行全部用例并检查结果。
PYTHONPATH=src python3 scripts/evaluate.py --provider deepseek --env-file .env \
  --case 01-clear --case 02-conflict --output-dir runs/deepseek-two-cases
```

接口采用非思考模式、`tool_choice=required`、`max_tokens`，标准端点不启用 Beta strict；本地仍严格校验参数和引用。模型每轮仍自行选择三个动作中的一个。配置依据核对于 **2026-10-28**：[DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)、[Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)。模型名称和账户可用性以供应商为准；缺密钥、HTTP 错误或网络错误不会自动降级为 Mock。

可选的 `--provider openai` 适配器使用 `OPENAI_API_KEY`、`OPENAI_MODEL`、可选 `OPENAI_BASE_URL`；本项目主验收提供方为 DeepSeek。该兼容入口没有做真实网络验收。

### 本次连接问题与离线重评

2026-10-29 首次预检遇到 Python 默认 CA 路径缺失；使用系统证书包后收到了 HTTP 402。用户处理 API 余额后完成完整真实运行。两次失败记录分别保存在 [live-preflight](examples/live-preflight/summary.md)、[live-preflight-ca](examples/live-preflight-ca/summary.md)，不算作模型决策证据。402 的含义见 [DeepSeek 官方错误码](https://api-docs.deepseek.com/zh-cn/quick_start/error_codes/)。

如果本机 Python 出现 TLS 证书错误，并且 `/etc/ssl/cert.pem` 存在，可以在进程环境中指定受信任系统证书包；其他平台使用自己的 CA 配置。保留 TLS 证书校验。

```bash
SSL_CERT_FILE=/etc/ssl/cert.pem PYTHONPATH=src python3 scripts/evaluate.py \
  --provider deepseek --env-file .env --output-dir examples/live-new

# 复现断言修正后的重评：不联网、不读密钥，原样复制输入/输出/Trace。
PYTHONPATH=src python3 scripts/evaluate.py --provider deepseek \
  --recheck-from examples/live-initial --output-dir runs/recheck
```

## 复现验证、故障与上下文

```bash
# 执行测试，并保存真实测试日志和机器可读摘要。
PYTHONPATH=src python3 scripts/test.py

# 执行全部离线验收，刷新 examples/mock/；预期 11/11。
PYTHONPATH=src python3 scripts/evaluate.py --provider mock

# 上下文追问，输入文件包含 question 与 history。
PYTHONPATH=src python3 -m knowledge_agent --provider mock \
  --input examples/mock/05-context-follow-up/input.json --output-dir runs/follow-up

# 检索只失败一次；由模型/替身观察错误后决定是否再试。
PYTHONPATH=src python3 -m knowledge_agent --provider mock \
  --question '正式员工一年有多少天带薪年假？' \
  --fail-tool search_documents:1 --output-dir runs/transient

# D02 持续读取失败；D01 的已读证据保留，最终 tool_error。
PYTHONPATH=src python3 -m knowledge_agent --provider mock \
  --question '报销材料应在多少天内提交？' \
  --fail-tool read_document:D02:always --output-dir runs/failure

# 上限耗尽明确未完成。finish 和无效动作尝试也占工具调用预算。
PYTHONPATH=src python3 -m knowledge_agent --provider mock \
  --question '年假有几天？' --max-steps 1 --output-dir runs/limit
```

退出码：`0` answered；`2` 输入/配置错误；`3` 需要澄清或资料外；`4` 工具/模型/记录写入错误；`5` 达到执行上限。业务未完成状态会正常生成输出文件，但返回非零退出码。

## 设计边界

- 使用原生 Python 实现，未采用 Agent 框架、向量数据库或多 Agent。`search_documents` 检索，`read_document` 读取短片段，`finish` 交付结果。
- 同义词扩展和中文双字匹配适合当前小型合成库。`policy_key` 与 `scope` 由资料维护者标注；同键同范围的不同原文会保守地视为待核实差异，即使只是措辞不同。它不是通用语义冲突检测器。
- 事实答案从模型选出的完整原文片段渲染，不接受模型自由填写事实答案；检查“已读取、ID 正确、原文一致、版本一致”。**引用真实不等于选材一定相关，也不等于检索完整**；模型相关性、范围判断和开放域效果需要真实评测与人工检查。
- 所有制度、产品名称和数值均为合成测试资料，不代表小影真实制度或产品承诺。没有线上服务、生产权限体系或长期会话存储。

## 提交 GitHub

代码和所有验收资料位于 [gehengxuan/xiaoyinbishi](https://github.com/gehengxuan/xiaoyinbishi) 的 `main` 分支。提交内容为：**题号 3、该 GitHub URL、最终 commit SHA**。SHA 获取方式与个人记录说明见 [06-submission.md](docs/06-submission.md)。
