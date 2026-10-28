# 企业知识问答 Agent · 小影校招项目题 3

Python CLI：模型选择检索或读取工具，观察实际返回后继续查证、追问或结束。答案带文档 ID、版本日期和原文片段；冲突无优先级时请求确认，工具失败和达到上限时明确返回未完成。

**交付状态：代码、离线测试及运行记录已完成；DeepSeek 真实模型验收、GitHub 远端提交仍待完成。** 离线 Mock 只验证流程，不能证明真实模型的 ReAct 决策效果。不要将 `examples/mock/` 当作真实模型运行记录。

## 评审入口

| 内容 | 入口 |
|---|---|
| 实际离线验收结果、11 条不同输入 | [examples/mock/summary.md](examples/mock/summary.md) |
| 明确答案：检索 → 读取 → 回答 | [01-clear/trace.md](examples/mock/01-clear/trace.md) |
| 冲突：读取双方 → 补查 → 追问 | [02-conflict/trace.md](examples/mock/02-conflict/trace.md) |
| 持续失败：保留已读资料 → 未完成 | [07-persistent-tool-failure/trace.md](examples/mock/07-persistent-tool-failure/trace.md) |
| 自动化测试实际输出 | [examples/test-results.txt](examples/test-results.txt) |
| 需求 / 设计 / 评估 | [01](docs/01-requirements.md) · [02](docs/02-solution.md) · [03](docs/03-evaluation.md) |
| AI 使用与个人贡献边界 / 复盘 | [04](docs/04-ai-usage.md) · [05](docs/05-retrospective.md) |

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

# 完整验收：会实际调用 API，生成 examples/live/ 的输入、输出、Trace 和检查结果。
PYTHONPATH=src python3 scripts/evaluate.py --provider deepseek --env-file .env

# 先检查两条真实路径也可以；完整交付仍应运行全部用例并检查结果。
PYTHONPATH=src python3 scripts/evaluate.py --provider deepseek --env-file .env \
  --case 01-clear --case 02-conflict
```

接口采用非思考模式、`tool_choice=required`、`max_tokens`，标准端点不启用 Beta strict；本地仍严格校验参数和引用。模型每轮仍自行选择三个动作中的一个。配置依据核对于 **2026-10-28**：[DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)、[Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)。模型名称和账户可用性以供应商为准；缺密钥、HTTP 错误或网络错误不会自动降级为 Mock。

可选的 `--provider openai` 适配器使用 `OPENAI_API_KEY`、`OPENAI_MODEL`、可选 `OPENAI_BASE_URL`；本项目主验收提供方为 DeepSeek。该兼容入口没有做真实网络验收。

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

代码和所有验收资料位于同一仓库。推送你指定的 GitHub 仓库后，提交：**题号 3、GitHub URL、最终 commit SHA**。获取方式和剩余步骤见 [06-submission.md](docs/06-submission.md)。
