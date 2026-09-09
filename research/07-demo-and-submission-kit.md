# Wallet Vitals — ETHOnline 2026 演示与提交材料

这份文件供比赛完成后录制和提交使用。凡是带方括号的内容都要换成最终事实。没有实现的功能整段删除。不能把计划写成已经完成的工作。

## 演示要让评委记住什么

用户无需注册、连接钱包或签名，只需在公开网页粘贴地址。服务端从 The Graph 查询实时 Aave 数据，说明当前风险、与上一快照相比发生了什么变化、在限定假设下离 health factor 1 还有多大 Liquidation Buffer，并在抵押资产下跌 5%、10%、20% 时重算 health factor。AI 只解释这些确定性结果并引用证据。核心完成后，Uniswap 提供无签名的去杠杆预览，Bazantic 让代理调用同一工作流。每份报告都带 Evidence Receipt；The Graph 查询失败或数据过旧时，页面停止分析并说明原因。

这句话要贯穿视频。其余信息只负责证明它是真的。

## 录制前的事实检查

- [ ] 视频中的钱包数据来自录制当时的实时 Graph 查询。
- [ ] 画面能看见 Subgraph ID、区块号或查询时间。
- [ ] AI 解释中的数字与确定性风险结果一致。
- [ ] Risk Delta 展示的两份快照同 market/deployment/schema 且 block 递增。
- [ ] Stress Ladder 画面明确显示抵押价格下跌、债务价值不变等假设。
- [ ] Liquidation Buffer 与 Stress Ladder 使用同一假设，并明确不是安全保证或价格预测。
- [ ] Evidence Receipt 显示 deployment、block/time、queried at、rules version 和 evidence refs。
- [ ] 至少展示一次“什么先失守”或等价引导追问，AI 回答引用 evidence refs。
- [ ] 用不暴露密钥的方式短暂展示 Graph 失败时分析停止。
- [ ] 所有声称完成的命令、测试和部署都能在公开仓库复现。
- [ ] `PRE_EXISTING.md` 与 Git 历史已经公开。
- [ ] API key、模型 key、钱包私钥和环境变量值没有进入 HTML、浏览器网络面板或录制画面。
- [ ] 若没有完成 Substreams，视频和提交文案完全不提 composable track。
- [ ] 若 Uniswap 或 Bazantic 未通过资格 Gate，视频和提交文案完全删除对应功能与 Sponsor。
- [ ] 最终视频在两分钟到四分钟之间，分辨率不低于 720p。
- [ ] 使用真人口播，不使用 AI 配音。

## 三分五十五秒 Prize Magnet 主版本

目标时长约三分五十五秒。正常语速录制，删除网络等待，不加速声音。

| 时间 | 画面 | 口播 | 评委看到的证据 |
|---|---|---|---|
| 0分00秒到0分18秒 | 打开公开首页；画面显示 No sign-up、No wallet connection | 一个钱包地址可能同时有抵押物、债务和不断变化的清算风险。Wallet Vitals 不要求注册或连接钱包，粘贴公开地址就能分析。 | 零摩擦产品入口 |
| 0分18秒到0分33秒 | 上游仓库、baseline tag、`PRE_EXISTING.md` | 这个项目延续了一个 2023 年的开源钱包跟踪器。原项目提供钱包登记、SQLite 和轮询概念。比赛期间新增的 Web、The Graph、Aave 风险计算和 AI 解释都能在 baseline 之后看到。 | Continuity 边界和 Git 历史 |
| 0分33秒到0分55秒 | 粘贴 `[REAL_ADDRESS]`，点击 Analyze live position | 我现在分析一个真实 Ethereum 地址。这里没有测试数据。服务端先检查 The Graph 索引位置，再查询 Aave V3 用户仓位和储备参数。 | 真实地址、真实请求、无需账号 |
| 0分55秒到1分25秒 | Web 报告显示当前仓位、健康因子、Liquidation Buffer 和 Risk Delta | 这份报告先显示协议原生健康因子和限定假设下的清算缓冲，再对比两份可比 Graph 快照。它不制造一个看似精确的综合分数，也不会猜测变化原因。 | 当前风险、变化证据与可记忆数字 |
| 1分25秒到1分48秒 | 放大 Stress Ladder | 这三行不是价格预测。它们与清算缓冲使用同一个风险核心，只在抵押资产价格统一下调百分之五、十和二十，债务价值不变时重算健康因子。 | 透明压力假设与确定性数学 |
| 1分48秒到2分08秒 | 放大 Evidence Receipt 中的 deployment、evidence id、block 和 queried at | 每条判断都能追到证据。如果数据过旧、索引报错或 Graph 无法访问，分析会直接停止。 | The Graph 是必要依赖 |
| 2分08秒到2分28秒 | 点击“什么先失守”；随后短暂展示 Graph 失败状态 | AI 只根据这份报告回答，并引用压力情景和证据编号。现在关闭 Graph 数据路径，分析会停止，而不是用缓存或 RPC 假装成功。 | AI 的实际作用与 load-bearing 证明 |
| 2分28秒到2分52秒 | 打开 De-risking Preview，展示真实 Uniswap 路由、输入输出和价格影响 | 风险引擎先算恢复目标健康因子所需的债务减少量，再请求实时 Uniswap 预览。它同时考虑卖出抵押物和偿还债务，但不连接钱包、不签名，也不执行交易。 | Uniswap 是风险到行动的真实延伸 |
| 2分52秒到3分12秒 | Bazantic 中运行 Recipe，从同一地址得到报告与预览 | 同一个结构化 API 也通过 Bazantic gateway 提供给代理。这个 Recipe 告诉代理何时分析、如何核验证据，以及何时请求去杠杆预览。 | 代理可复用的工作流，不是第三套产品 |
| 3分12秒到3分32秒 | 一张简洁数据流图，突出三 Sponsor 的先后关系 | The Graph 提供事实，风险引擎做确定性计算，Uniswap提供实时路线，Bazantic 让代理复用同一链路。任何扩展失败都不会伪造核心报告。 | 一个项目、一条价值链、三个自然奖项 |
| 3分32秒到3分45秒 | 终端运行测试，随后快速展示提交历史 | 测试覆盖 Aave 数学、报价边界、Graph 错误和匿名可靠性。仓库保留逐步提交、Continuity 边界与 Sponsor 代码指针。 | 技术完成度和可复现性 |
| 3分45秒到3分55秒 | 回到公开 Web 报告和仓库地址 | 最终得到的是一个任何人都能打开、代理也能调用、每一步都可核验的风险助手。 | 清楚收尾 |

## 连续中文口播稿

一个钱包地址可能同时有抵押物、债务和不断变化的清算风险。Wallet Vitals 不要求注册、连接钱包或签名。任何人粘贴公开地址，就能得到一份实时风险报告。

这个项目延续了一个 2023 年的开源钱包跟踪器。原项目提供钱包登记、SQLite 和轮询概念。比赛期间新增的无账号 Web、The Graph、Aave 风险计算和 AI 解释，都能在 baseline 之后的提交中看到。

我现在粘贴一个真实 Ethereum 地址并点击分析。这里没有测试数据。服务端会先检查 The Graph 的索引位置，然后查询 Aave V3 的用户仓位和储备参数。

这份报告显示当前抵押物、债务和健康因子，也给出限定假设下的 Liquidation Buffer。它还对比前后两份可比快照，列出观察到的 Risk Delta。这里没有一个缺少校准依据的综合风险分数，也不会在没有事件证据时猜测变化原因。

接着是 Stress Ladder。这不是价格预测。它与 Liquidation Buffer 使用同一个风险核心，只在抵押资产价格统一下调百分之五、十和二十，债务价值不变的假设下重算健康因子。AI 只读取已经算好的结果和证据，不能修改数字。

每条判断都能追到 Evidence Receipt。这里可以看到 Aave Subgraph deployment、查询区块、时间、规则版本和情景假设。如果数据过旧、索引报错或 Graph 无法访问，分析会直接停止。

我现在问它什么先失守。AI 会从本次压力情景和变化证据中挑出最重要的观察，并引用 evidence id。再短暂关闭 Graph 数据路径，分析会明确停止，而不是改用缓存或 RPC 假装成功。

核心报告稳定后，风险引擎先计算恢复目标健康因子所需减少的债务，再向 Uniswap 请求真实转换预览。它会显示输入、预期输出、路线和价格影响，但不连接钱包、不签名，也不广播交易。

同一个结构化 API 还通过 Bazantic gateway 提供给代理。Recipe 让代理从地址开始，读取风险和证据，并在适用时请求同一份去杠杆预览。普通 Web 不依赖 Bazantic 账号或支付。

整条路径仍然只有一套风险核心。The Graph 提供事实，风险引擎计算当前风险、Risk Delta 和 Stress Ladder，Uniswap提供实时路线，Bazantic 让代理复用同一链路。SQLite 保存快照和有保留期的匿名报告。

测试覆盖 Aave 数学、快照可比性、压力情景、Graph 错误、数据陈旧、匿名限流、报告过期和幂等。仓库保留了逐步提交，也明确列出原有代码和比赛新增代码。

最终得到的是一个任何人都能打开、代理也能调用、每一步都能核验的钱包风险助手。代码、测试和复现步骤都在公开仓库里。

## 两分三十秒核心备用版本

网络或录制时间紧张时，删掉第二个地址和架构图，保留 Risk Delta、Liquidation Buffer、Stress Ladder、AI 引导问题和 Evidence Receipt。

1. 十五秒说明用户问题。
2. 十五秒说明上游基线和比赛新增工作。
3. 六十秒完成首页输入、实时分析和报告生成。
4. 二十五秒展示 Risk Delta、Stress Ladder 和 Evidence Receipt。
5. 二十秒展示数据流。
6. 十五秒展示测试、Git 历史和公开仓库。

这个版本仍然要展示 AI 输出和实时 Graph 数据。不能用 fixture、截图或预先写好的 JSON 替换真实查询。若最终选择 Uniswap 或 Bazantic Partner Prize，不使用这个版本提交，因为它没有足够时间证明对应资格；应修复并使用三分五十五秒版本。

## 录制故障处理

### Graph 查询太慢

提前录下一段同日真实查询，把等待部分剪掉。保留地址提交、Web 响应、区块和时间。口播不能把剪辑说成即时零延迟。

### Web 页面加载失败

先修复再录。终端打印 JSON 或 Swagger 页面不能代替核心 Web 体验。提交前至少录到一次首页输入、加载、报告和引导问题的完整路径。

### 找不到真实高风险钱包

展示普通仓位也可以。解释当前健康因子以及哪些变化会使它进入 warning 或 danger。不能调整阈值来制造高风险，也不能把固定 fixture 当作实时钱包。

### Risk Delta 没有明显变化

不依赖主动提醒。提前积累同一真实地址的两份可比 Graph 快照，并展示真实 Risk Delta；没有变化时如实展示零变化，不手工修改结果。

### AI 服务临时失败

先展示确定性 fallback，说明数值仍然可用。最终提交视频还要补录一次正常 AI 解释，否则无法充分证明 AI track 的核心能力。

## 英文一句话介绍

建议使用下面这句，它同时说清交互形态、差异化能力和核心数据源。

> An accountless, evidence-grounded Aave risk copilot that explains what changed, what breaks first, and how to verify it using live The Graph data.

品牌标语可用：

> See what changed. Stress-test what could happen. Verify every result.

## 英文 Project Description 草稿

> Wallet Vitals revives an abandoned open source wallet tracker as an accountless, evidence-grounded Aave risk copilot. Anyone can paste a public Ethereum address without signing up or connecting a wallet. The app builds a current position report from live data queried through The Graph and compares compatible evidence snapshots to show observed changes in collateral, debt, and health factor. Under a clearly labeled static scenario, it calculates a Liquidation Buffer and runs deterministic collateral shocks of minus 5, 10, and 20 percent while holding debt value constant. These are sensitivity tests, not predictions or safety guarantees. Instead of inventing a composite risk score, the app preserves Aave's health factor and deterministic severity rules. An AI narrator explains the calculated results, answers a guided question, and cites evidence without changing the numbers or inventing causes. Every report includes an Evidence Receipt with the Graph deployment, source block and time, query time, rules version, scenario assumptions, and evidence references. The Graph is load bearing. If the Aave Subgraph is unavailable or stale, the analysis stops and reports the failure. [If completed: A live Uniswap de-risking preview estimates the collateral-to-debt conversion required for a target health factor without connecting a wallet or executing a transaction. The same evidence-grounded API is exposed through a Bazantic gateway and Recipe so agents can run the workflow.] The original repository supplied wallet registration, SQLite, and polling concepts. All event-period work is documented in PRE_EXISTING.md.

录制前删除所有没有完成的句子。若报告永久链接、ENS 或自由文本追问未完成，删除对应句子，不把计划写成事实。

## 英文 How It’s Made 草稿

> The application runs as a single Python 3.12 FastAPI service. Server-rendered templates, static CSS, and a small amount of browser JavaScript provide an accountless interface; Graph and model credentials remain server-side. A shared asynchronous HTTP client queries the official Aave V3 Ethereum Subgraph through The Graph Network. Each response is validated together with its block and indexing metadata, then normalized into an immutable evidence snapshot. A pure risk engine calculates collateral value, debt value, liquidation-weighted collateral, health factor, deterministic severity, and a scenario-limited Liquidation Buffer using fixed-point arithmetic. A delta module compares only compatible, block-ordered snapshots. A stress module reuses the same health-factor core under three explicitly labelled collateral-only price shocks while holding debt value constant. The AI layer receives only those calculated results and selected evidence. [If completed: A separate Uniswap adapter requests live routes only after the risk engine solves the target-health-factor conversion, and a Bazantic gateway plus Recipe exposes the same API to agents.] SQLite stores snapshots and expiring anonymous reports. Tests cover Aave math, snapshot comparability, buffer and stress assumptions, Graph errors, quote failures, rate limits, report persistence, and secret leakage. The repository preserves the upstream MIT license, an unchanged baseline tag, and a PRE_EXISTING.md disclosure that separates prior work from the event implementation.

只有完成部署后，才在末尾补充实际部署平台和运行地址。只有真正通过资格验收后，才保留 Uniswap、Bazantic 或其他 Sponsor 段落。

## 英文 Continuity 披露短段

> This submission extends `dorukyy/telegram-wallet-tracker` at upstream commit `c96f64078ffcf1cc3090778591ad4971ac48292f`. The upstream project provided Telegram wallet registration, SQLite storage, and basic polling against legacy chain APIs. It did not include The Graph, Aave position normalization, risk scoring, AI explanations, evidence references, or reliable alert deduplication. Event period work is visible after the `upstream-baseline` tag and is described in PRE_EXISTING.md.

## 评委常见问题

### The Graph 为什么是必要依赖

用户可见的 Aave 仓位、储备参数和风险证据都来自实时 Subgraph。系统没有 RPC 或 Etherscan 的静默替代路径。Graph 失败时，报告会停止并标出错误。

### AI 做了什么

风险引擎先做数值计算、快照差分和压力情景。AI 读取这些结果，选择最重要的观察变化，解释它们为什么值得关注，并把每项判断连到 evidence id。没有事件证据时，AI 不能猜测变化原因；它也不能修改数值或补齐缺失数据。

### 与现有 Aave 监控器有什么不同

现有产品已经能显示 health factor 和发送阈值提醒。Wallet Vitals 的核心不是再做一个数字看板，而是无需账号就能比较可复核的 Graph 快照、运行明确假设的压力情景，并为每份结果提供 Evidence Receipt。没有足够证据时，它拒绝归因或继续分析。

### 原项目贡献了什么

原项目贡献了公开钱包跟踪、SQLite 和轮询比较的产品概念。比赛期间完成无账号 Web、The Graph 数据层、Aave 数学、风险规则、AI 解释、匿名可靠性、测试和部署。最终答案以 Git diff 和 `PRE_EXISTING.md` 为准。

### 为什么不用 RPC

项目要让结构化、可查询的 Graph 数据承担核心工作。Subgraph 同时给出用户仓位、储备参数和索引位置，风险报告可以记录明确的数据来源。RPC 只会增加另一条难以证明的正式路径。

### 如何保证风险数字可信

计算使用固定精度整数和 Decimal。测试覆盖零债务、稳定债务、变量债务、抵押开关、陈旧数据和索引错误。真实钱包结果还会与 Aave 官方界面比较，超过既定误差就停止发布风险等级。

### 为什么没有 0–100 风险分数

没有公开校准数据时，综合分数会制造不必要的精确感。产品保留 Aave health factor、透明阈值、Liquidation Buffer 和固定压力情景，评委可以从同一份证据复算每个结论。

### fixture 是否违反实时数据要求

fixture 只用于单元测试和错误测试。正式运行、视频演示和评委复现都查询实时 Graph provider，并展示 block 和 queried at。

### 为什么从旧仓库开始

旧仓库已经有一个清楚的用户动作：保存公开钱包并周期性比较变化。它的数据接口和账号型 Bot 依赖已经失效，这给比赛期间重构为无账号 Web 留下了明确边界。新的价值可以从 Git 历史里逐项核验。

### 是否申报 composable track

[只在 Substreams 已完成时使用] Aave Subgraph 提供协议仓位，Pinax EVM Substreams 提供 Transfer 或 Approval 事件。Substreams 事件触发新的 Aave 快照和风险计算，并进入 Web 事件时间线，两种 Graph 产品共同影响报告。

[没有完成 Substreams 时使用] 本项目在 The Graph Sponsor 内只申报 AI Continuity pool，不申报 composable/standardized 子赛道。核心产品使用一个官方 Aave Subgraph，并对实时数据进行风险计算、自动化和 AI 解释。

## 最终提交检查

- [ ] Project Name 和英文一句话介绍已经定稿。
- [ ] Project Description 只写最终实现。
- [ ] How It’s Made 写明实际 Subgraph ID、模型、部署平台和测试命令。
- [ ] Source Code 指向公开仓库。
- [ ] Live Demo 指向无需登录即可访问的 HTTPS 页面。
- [ ] 视频长度已在导出文件上复核。
- [ ] 视频前二十秒已经进入问题和产品。
- [ ] 视频主体展示真实地址输入、真实 Web 响应和 Graph metadata。
- [ ] 视频展示 Liquidation Buffer、一个带证据引用的引导追问，以及 Graph 失效时的明确停止。
- [ ] 若选择 Uniswap，视频展示真实路线、目标 health factor 数学和无签名边界；`FEEDBACK.md` 与反馈表完成。
- [ ] 若选择 Bazantic，视频展示 gateway、Recipe 和可复核 A/B 结果；提交中提供所需用户名。
- [ ] 视频没有密钥、私钥、浏览器通知或个人信息。
- [ ] 视频声音清楚，没有 AI 配音和加速。
- [ ] 选择 The Graph 的 Continuity pool。
- [ ] 只有通过资格 Gate 时才选择 Uniswap Foundation 和 Bazantic；未完成即删除。
- [ ] 只有在真实组合两个 Graph 产品后才选 composable track。
- [ ] `PRE_EXISTING.md`、README、视频和提交页的说法一致。

## 官方参考

- [ETHOnline 2026 The Graph 奖项要求](https://ethglobal.com/events/ethonline2026/prizes/the-graph)
- [ETHOnline 2026 奖项总览](https://ethglobal.com/events/ethonline2026/prizes)
- [Prize Magnet 三 Sponsor 决策](13-prize-magnet-selection.md)
- [ETHGlobal 2026 提交与视频建议](https://ethglobal.com/events/newyork2026/info/details)
- [ETHGlobal Showcase 字段示例](https://ethglobal.com/showcase/project-name-vndcz)
