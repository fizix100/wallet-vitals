# Wallet Vitals — ETHOnline 2026 准备包

这是一组赛前研究文档，不包含参赛功能实现。目的，是在 ETHOnline 2026 开赛后能够快速、可审计地从现有开源项目出发，并清楚区分原项目能力与比赛期间新增工作。

项目名称：**Wallet Vitals**  
仓库名称：`wallet-vitals`  
产品形态：**无需账号、无需钱包连接的公开 Web 应用**  
英文一句话介绍：*An accountless, evidence-grounded Aave risk copilot that explains what changed, what breaks first, and how to verify it using live The Graph data.*

当前选择：以 [`dorukyy/telegram-wallet-tracker`](https://github.com/dorukyy/telegram-wallet-tracker) 作为 Continuity 基线，保留“输入公开钱包、保存快照、比较变化”的产品概念；比赛期间把失效的数据层和账号型 Bot 外壳重构为公开 Web 应用，并新增 The Graph 实时数据、确定性 Aave 风险分析和有证据引用的 AI 解释。

Partner Prize 目标：一套代码只选择三个自然重叠的 Sponsor——The Graph 负责实时 Aave 风险核心，Uniswap 提供无签名的去杠杆预览，Bazantic 把同一证据工作流开放给代理。三个集成都必须通过独立资格 Gate；缺少真实证据时宁可少选，不为凑数加入装饰功能。

审计基线：`c96f64078ffcf1cc3090778591ad4971ac48292f`（2023-09-23）。

## 文档

- [01-baseline-audit.md](research/01-baseline-audit.md)：原仓库已有能力、实测结果和技术风险。
- [02-PRE_EXISTING.draft.md](research/02-PRE_EXISTING.draft.md)：提交时可直接完善的英文披露草稿。
- [03-the-graph-migration-spec.md](research/03-the-graph-migration-spec.md)：The Graph 作为关键依赖的架构、范围和接口。
- [04-kickoff-and-acceptance-checklist.md](research/04-kickoff-and-acceptance-checklist.md)：开赛日留证流程、验收标准和提交门槛。
- [05-graph-data-source-screening.md](research/05-graph-data-source-screening.md)：候选 Subgraph、Substreams 与 Token API 的实时探针和优先级。
- [06-implementation-backlog.md](research/06-implementation-backlog.md)：冻结技术栈、模块边界、逐日计划与砍项规则。
- [07-demo-and-submission-kit.md](research/07-demo-and-submission-kit.md)，评委演示分镜、中文口播、英文提交文案与问答准备。
- [08-rules-recheck-and-test-wallets.md](research/08-rules-recheck-and-test-wallets.md)：最新截止时间、资格规则和开赛日公开测试地址。
- [09-competitive-positioning.md](research/09-competitive-positioning.md)：现有 Aave 监控产品、差异化核心、产品边界和评委叙事。
- [10-day-zero-runbook.md](research/10-day-zero-runbook.md)：开赛日前 90 分钟操作顺序、命令、停止条件与本机就绪状态。
- [11-win-rate-audit.md](research/11-win-rate-audit.md)：按官方评审维度做的胜率审计、优先级调整与演示优化。
- [12-accountless-web-pivot.md](research/12-accountless-web-pivot.md)：取消 Telegram 后的无账号 Web 产品决策、接口边界、隐私与迁移清单。
- [13-prize-magnet-selection.md](research/13-prize-magnet-selection.md)：按最多三个 Partner Prizes 反推的 Sponsor 组合、边际成本与资格 Gate。

## 当前边界

在官方开赛前，只做仓库筛选、运行审计、架构设计和披露准备。不开参赛分支，不实现 The Graph、AI 风险分析、Uniswap、Bazantic、仪表盘或其他比赛功能。

官方依据：

- [ETHOnline 2026 活动说明](https://ethglobal.com/events/ethonline2026/info/details)
- [The Graph 奖项要求](https://ethglobal.com/events/ethonline2026/prizes/the-graph)
- [ETHGlobal 官方规则](https://ethglobal.com/rules)
