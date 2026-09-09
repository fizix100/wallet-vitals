# 开赛日流程与验收清单

## 开赛前允许完成

- [x] 候选仓库筛选和许可证核对。
- [x] 上游运行审计与故障记录。
- [x] 原有能力和非原有能力盘点。
- [x] 架构、风险模型和验收标准草案。
- [x] `PRE_EXISTING` 披露草稿。
- [x] 重新确认活动日期、提交截止时间、官方赛道页面和规则更新；精确 kickoff 时刻仍需在开赛日从 Hacker Dashboard 记录。
- [x] 准备公开测试钱包地址，但不写参赛功能；地址与动态快照见 `08-rules-recheck-and-test-wallets.md`。

截至 2026-09-01，活动列表仍显示 ETHOnline 2026 为 9 月 4–16 日，但官方提交详情页写明提交截止时间为 9 月 13 日 12:00 EDT，即北京时间 9 月 14 日 00:00。实施和冻结计划以更早的提交截止时间为准，不能把 9 月 16 日当作可开发至最后一刻的日期。

## 开赛后的前 90 分钟

逐分钟命令与停止条件见 [`10-day-zero-runbook.md`](10-day-zero-runbook.md)。

1. 记录官方开始时间和当时的规则页面。
2. Fork 上游仓库，保留 MIT License 和 attribution。
3. 记录上游 commit，创建未修改的 `upstream-baseline` tag。
4. 在公开仓库加入完成版 `PRE_EXISTING.md`，提交为独立 commit。
5. 建立比赛分支，确认后续所有实现都有小而清晰的 Git commits。
6. 再验证 The Graph 候选实时数据源；保存最小查询、返回元数据和限制。
7. 将实际选择的数据源、网络和风险信号写入 README，再开始实现。

开赛日需要分别准备以下开发者侧凭据：

- Subgraph Studio API key：查询 The Graph Network 上的 Aave Subgraph。
- The Graph Market API token：只有启用 Token API 或 Substreams 时才需要。
- Uniswap Developer Platform API access：只有核心通过 G3 后才用于去杠杆预览。
- Bazantic 账号和 gateway 配置：只有核心与前两个 Sponsor 证据稳定后才创建 agent 通道。

两者均只放入环境变量或部署平台 secrets，不进入 Git 历史。

不要把所有开发压成一个最终大 commit。ETHGlobal 官方规则明确要求使用版本控制，并通过仓库历史、视频和描述披露既有工作。

## 功能验收

### 无账号 Web 入口

- [ ] 用户无需注册、登录、连接钱包或签名即可提交公开 EVM 地址。
- [ ] 合法地址可分析，并生成稳定的 `report_id` 与可重新打开的报告 URL。
- [ ] 非法地址和不支持的网络得到明确错误。
- [ ] 首次分析显示 `no_baseline`；重复分析不会制造重复或倒序快照。
- [ ] 浏览器永远看不到 Graph key、模型 key 或服务器内部错误细节。
- [ ] 页面在桌面和手机宽度下均能读完核心报告，不依赖 React 构建链。

### The Graph 数据链路

- [ ] 所有用户可见链上事实来自已记录的实时 Graph 数据源。
- [ ] 至少一个真实测试钱包能返回非空实时数据。
- [ ] 输出记录网络、数据源、block/time 和查询时间。
- [ ] 支持分页、空结果、超时、限流与重试。
- [ ] 禁用 Graph 数据源后，核心报告无法伪装为正常成功，以证明它是关键依赖。
- [ ] Demo 不使用 mock、静态 JSON 或本地伪造结果替代主链路。

### 风险引擎

- [ ] 每个规则有固定公式、阈值、版本和单元测试。
- [ ] 同一证据输入产生同一协议指标、派生指标、风险等级和触发结果。
- [ ] MVP 不展示缺少公开校准依据的 0–100 综合风险分数。
- [ ] 缺失或陈旧数据不会被当作低风险。
- [ ] 每个结论能定位到一条或多条 evidence。
- [ ] 至少一个正常、一个高风险、一个数据不完整场景通过测试。
- [ ] Risk Delta 只比较同钱包、同 market、同 deployment/schema 且 block 递增的快照。
- [ ] 无前序快照返回 `no_baseline`，不把当前值伪装成变化。
- [ ] Stress Ladder 固定测试抵押价格 -5%、-10%、-20%，并在用户输出中明示“债务价值不变”等假设。
- [ ] Liquidation Buffer 复用同一健康因子核心和情景假设；零债务、不完整证据或 health factor 小于等于 1 时返回明确状态。
- [ ] 压力情景不被表述为价格预测、安全保证、清算时间或个性化投资建议。
- [ ] Evidence Receipt 包含 deployment、block/time、queried at、rules version、scenario assumptions 和 evidence refs。

### AI 层

- [ ] AI 输出只使用结构化 evidence 和已计算结果。
- [ ] 每项重要判断引用 evidence id 或关键数字。
- [ ] 数据不足时明确说“不足以判断”。
- [ ] 防止提示注入内容从链上字段改变系统规则。
- [ ] AI 失败时仍可返回确定性风险报告。
- [ ] 输出包含有意义的分析或建议，不只是打印 Graph 查询结果。
- [ ] AI 只能把 Risk Delta 写成“观察到的变化”；没有事件证据时不声称具体原因。
- [ ] 至少一个引导追问能回答“什么先失守”或“如何核验”，且答案引用本次报告的 evidence refs。

### Web 与可靠性

- [ ] 匿名请求有并发上限、地址冷却时间和明确的 429/重试提示。
- [ ] 报告 URL 不包含任何 API key、模型 key 或内部凭据。
- [ ] 服务重启后已有报告和快照仍可读取，过期策略明确。
- [ ] API key 和模型密钥不进入仓库、HTML、浏览器网络响应或错误页。
- [ ] 日志不泄漏密钥或完整敏感配置。

### Uniswap 去杠杆预览，条件验收

- [ ] 先由风险引擎计算恢复目标 health factor 所需的债务减少量，再请求真实 Uniswap 路由；不能用固定数量凑演示。
- [ ] 计算同时考虑抵押物卖出和债务偿还对 health factor 的影响，并有单元测试。
- [ ] 报告显示输入、预期输出、路由、价格影响、报价时间和仅为预览的说明。
- [ ] 报价失败、无路由或流动性不足时明确不可用，不影响核心风险报告。
- [ ] 项目不连接用户钱包、不签名、不广播交易。
- [ ] `FEEDBACK.md`、官方反馈表和 README 代码指针全部完成。

### Bazantic agent 通道，条件验收

- [ ] 现有分析 API 通过 Bazantic x402/MPP Gateway 暴露，不复制风险逻辑。
- [ ] Recipe 能从地址生成风险报告，并在可用时请求 Uniswap 去杠杆预览。
- [ ] raw API 与 Recipe 使用相同 prompt、模型、设置和 API access 完成 A/B 测试。
- [ ] 输入、输出、改进说明和完整录屏可公开复核。
- [ ] gateway 或 Bazantic 失败不影响普通无账号 Web。

## 提交门槛

- [ ] 公开仓库可访问，许可证和上游 attribution 清楚。
- [ ] README 明确列出 pre-existing 与 event-period work。
- [ ] README 给出一条可复现的本地启动路径。
- [ ] Live Demo URL 无需账号即可打开，首页能直接输入公开地址。
- [ ] README 写明实际使用的 Graph 产品、数据源和它们为何是关键依赖。
- [ ] 自动测试在干净环境通过，并记录命令。
- [ ] 2–4 分钟视频展示真实端到端路径、实时 Graph 数据和 AI 推理结果。
- [ ] 视频至少展示一份 Risk Delta、Stress Ladder 和 Evidence Receipt，不只展示当前 health factor。
- [ ] 视频或提交描述指出 baseline tag 与最终 tag。
- [ ] 最终 repo diff 与 `PRE_EXISTING.md` 一致。
- [ ] 默认选择 The Graph、Uniswap Foundation、Bazantic 三个 Partner Prizes；任一未通过对应资格验收就从提交中删除。

## Go / No-Go 决策

在开赛后第一轮数据源验证结束时：

- **Go**：实时 Graph 数据足以完整支持至少一个高价值风险信号，并能在无需账号的 Web 页面展示证据闭环。
- **Narrow**：只支持 Aave 或单一活动类型时，缩成一个可信的协议风险助手，不扩展假能力。
- **No-Go / 收缩界面**：数据源无法稳定复现，或 Web 界面吞噬主要时间；此时保留同一 Graph 风险核心，改用最小服务端 HTML 和 JSON API，不切换到新的账号型平台。

官方参考：[活动说明](https://ethglobal.com/events/ethonline2026/info/details)、[奖项总览](https://ethglobal.com/events/ethonline2026/prizes)、[三 Sponsor 选择](13-prize-magnet-selection.md)、[官方规则](https://ethglobal.com/rules)。
