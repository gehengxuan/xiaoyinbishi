# 06 · 提交状态与操作

## 当前状态

- 题号：**3 · 企业知识问答 Agent**。
- 已完成：本地代码、依赖/环境示例、可执行测试、11 条实际离线运行记录、五份必需文档、离线 CI 配置。
- 待完成：真实 DeepSeek API 验收、候选人个人修改/验证及手工用时、指定 GitHub 仓库推送。
- GitHub URL：尚未提供或创建，不虚构链接。
- 最终 SHA：推送完成后读取 `git rev-parse HEAD`；不要使用文档中的旧 SHA 代替最终提交。

## 补齐真实模型与个人记录

在本机 `.env` 配置密钥后运行：

```bash
PYTHONPATH=src python3 scripts/evaluate.py --provider deepseek --env-file .env
```

核对 `examples/live/` 实际输出，将真实运行结果、失败和限制补入 `03-evaluation.md`；如本人有修改与独立验证，更新 `04-ai-usage.md`、`05-retrospective.md` 和用时。现有文档已明确当前 AI 实现范围，不能据此声称个人独立实现。

## GitHub 提交

先在你选择的 GitHub 账号下准备一个可供评审读取的仓库。以下远端 URL 是需替换的占位示例，当前未执行推送。

```bash
git status --short
git check-ignore .env
# 替换为你自己的仓库地址；如果已经有 origin，先用 git remote -v 核对。
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git add .
git commit -m 'Complete knowledge QA agent submission'
git push -u origin HEAD
git rev-parse HEAD
```

若所有更改已经提交，省略 `git add` / `git commit`。本地 `.env` 必须继续被忽略，不得为了提交而强制添加。私有仓库需要按试卷要求给指定评审账号读取权限；评审账号尚未提供，当前没有修改任何账号权限。

最终提交文本：题号 3、真实 GitHub URL、上述命令得到的完整 SHA。代码、资料与所有运行记录应在同一仓库内。
