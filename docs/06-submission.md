# 06 · 提交状态与操作

## 当前状态

- 题号：**3 · 企业知识问答 Agent**。
- 已完成：本地代码、环境示例、45 项测试、11 条离线与 11 条真实 DeepSeek 运行记录、五份必需文档、离线 CI 配置。真实记录首轮 10/11，修正过窄断言后原样重评 11/11。
- 已推送：`main` 分支；本地 `origin` 指向下列仓库。
- GitHub URL：[https://github.com/gehengxuan/xiaoyinbishi](https://github.com/gehengxuan/xiaoyinbishi)。
- 待补充：候选人个人修改/独立验证及手工用时。
- 最终 SHA：读取 `git rev-parse HEAD` 并与远端 main 对照；不要使用旧 SHA 代替最终提交。

## 复核真实模型与补充个人记录

本次真实验收已经完成，见 [review.md](../examples/live/review.md)。如需重新运行，请使用新目录保留已提交记录；当前 macOS Python 使用系统 CA：

```bash
SSL_CERT_FILE=/etc/ssl/cert.pem PYTHONPATH=src python3 scripts/evaluate.py \
  --provider deepseek --env-file .env --output-dir examples/live-new
```

核对 `examples/live/` 实际输出，将真实运行结果、失败和限制补入 `03-evaluation.md`；如本人有修改与独立验证，更新 `04-ai-usage.md`、`05-retrospective.md` 和用时。现有文档已明确当前 AI 实现范围，不能据此声称个人独立实现。

## GitHub 提交

已按用户指定命令配置远端、将分支重命名为 main 并完成推送。后续如有更改，应先提交，再推送并核对 SHA：

```bash
git status --short
git check-ignore .env
git remote -v
git push origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

本地 `.env` 必须继续被忽略，不得为了提交而强制添加。私有仓库需要按试卷要求给指定评审账号读取权限；评审账号尚未提供，当前没有修改任何账号权限。

最终提交文本：题号 3、真实 GitHub URL、上述命令得到的完整 SHA。代码、资料与所有运行记录应在同一仓库内。
