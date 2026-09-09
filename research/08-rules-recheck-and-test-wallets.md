# ETHOnline 2026 规则复核与测试钱包

复核时间：2026-09-02，Asia/Shanghai。本文只记录赛前研究、公开地址和只读链上快照，不包含参赛功能实现。

## 需要立即采用的结论

1. ETHGlobal 活动列表显示 ETHOnline 2026 的活动日期为 9 月 4–16 日。
2. 官方提交详情页给出的提交截止时间是 **2026-09-13 12:00 EDT**，换算为北京时间是 **2026-09-14 00:00**。
3. 两个日期存在表面差异时，以更早、且明确标为 Submission Deadline 的时间控制开发和提交。
4. 内部提交目标定为 9 月 13 日 10:00 EDT，保留两小时处理上传、视频或平台故障。
5. 官方公开页面尚未给出精确 kickoff 时刻。开赛日必须从 Hacker Dashboard 或正式 kickoff 通知记录该时刻，再进行 fork、baseline tag 和首个 event-period commit。

## 2026-09-02 Partner Prize 复核

- 官方提交详情仍写明 2026-09-13 12:00 EDT 截止，未发生变化。
- The Graph 页面仍把 From Scratch 与 Continuity 列为独立的 AI 奖池；本项目应选择 `Best AI Tooling or AI Use Case with The Graph (Continuity)`，不能误选同名的 From Scratch 奖池。
- Continuity 资格文字仍要求 The Graph 是关键依赖、消费 Graph provider 的实时数据、对数据执行有意义的推理或交互，并提交公开仓库和 2–4 分钟视频。
- ETHGlobal 公共活动页与公开信息中心仍未显示精确 kickoff 时刻；只有登录后的 Hacker Dashboard 或官方 kickoff 通知可以作为开赛证据。
- 官方确认每个项目最多选择三个 Partner Prizes；同一 Partner 的多个 track 只占一个名额。
- 默认 Sponsor 组合调整为 The Graph、Uniswap Foundation 和 Bazantic。Uniswap 只做无签名去杠杆预览，Bazantic 只包装同一 API；两者必须在核心完成后通过独立 Gate。
- ENS 当前要求 ENSv2 Sepolia 成为核心，Arc agent track 要求钱包、USDC 与真实交易，因此不属于低成本重叠项。
- 详细组合依据见 [13-prize-magnet-selection.md](13-prize-magnet-selection.md)。

## 资格与提交规则快照

- Continuity Track 可以扩展现有开源仓库，但必须清楚披露既有工作，并在活动期间开发实质性新功能。
- 必须使用版本控制。大而单一的提交或缺失历史可能导致失去资格。
- 使用 AI 开发工具是允许的，但要说明使用范围；参赛者仍需作出有意义的产品、架构、实现和验证贡献。
- Spec-driven development 若用于实现，需把相关规格、提示和规划材料放入提交仓库。
- Demo 视频必须为 2–4 分钟且至少 720p；不能用 AI 配音、手机录制或加速声音来压缩时长。
- 最多选择三个 Partner Prizes。
- The Graph AI Continuity 要求 The Graph 是 load-bearing，使用 Graph provider 的实时数据，并对数据执行推理、决策、自动化或自然语言交互。只打印查询结果不合格。
- 单独查询一个非标准化 Subgraph 不符合 composable/standardized 奖项要求，但可以符合 AI Continuity。本项目因此继续把 AI Continuity 作为主目标。
- Uniswap 与 Bazantic 未通过各自资格验收时不得在提交表单选择，即使只差文档或录屏也不能把计划写成完成。

## 公开测试钱包候选

以下地址来自公开的近期 Aave V3 Ethereum 清算记录或公开知名地址。赛前只使用 Ethereum RPC 对 Aave V3 Pool 的 `getUserAccountData` 做存在性预筛。该预筛不能替代开赛后必须完成的 The Graph 实时查询，也不会进入产品正式数据路径。

预筛快照：Ethereum block `25882756`，`2026-09-01T13:33:35Z`。美元数值来自 Aave V3 Pool 的 8 位 base currency 精度；health factor 按 18 位精度换算。

| 用途 | 地址 | 抵押价值 | 债务价值 | Health factor | 选择理由 |
|---|---|---:|---:|---:|---|
| 空仓位控制组 | `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` | $0.00 | $0.00 | 无有限值 | 公开知名地址，用来验证空结果和零债务行为。 |
| 接近清算边界 | `0x8327e20a05516c9be8dd305e517cd742b629e00f` | $1,671.45 | $1,358.80 | 1.020981 | 快照时非常接近 1，适合验证危险级别；仓位可能很快变化或清空。 |
| 小额风险仓位 | `0xc950fe241c50f93d872edb5a97066474c84c2394` | $6,567.20 | $4,814.44 | 1.132173 | 数值规模适中，适合人工核对与 Web 演示。 |
| 较大复杂仓位 | `0x552b42287c4fe1e913ea9a159b69bd7e9b81ec76` | $254,123.62 | $179,968.02 | 1.114981 | 适合验证多资产、较大数值和最近清算后的状态变化。 |
| 大额对照仓位 | `0x27b06e8d52d6ed7ba65b43ad30af71bbe607f687` | $7,409,695.66 | $4,800,860.98 | 1.203859 | 适合检查大额精度、性能和消息截断，不建议作为默认公开视频地址。 |

这些地址均是第三方公开账户，不代表地址所有者同意或认可本项目。产品只分析公开链上事实，不推断身份、意图、财务能力或违法行为。

## 开赛日重新验证顺序

1. 先用 Studio API key 查询官方 Aave V3 Ethereum Subgraph 的 `_meta`，确认 block 新鲜且无 indexing error。
2. 对五个候选地址执行同一份最小 `userReserves` 查询，记录非空结果、block、query time 和 schema 差异。
3. 至少保留一个空仓位、一个普通非空仓位和一个较低 health factor 仓位。已经还款、清算完毕或无法由 Graph 返回的地址立即替换。
4. 用 Aave 官方界面或 Pool 的只读 `getUserAccountData` 进行独立对照，但不得把 RPC 结果作为产品的静默 fallback。
5. 任何余额、债务和 health factor 都只绑定到本次查询的区块和时间，禁止硬编码为测试预期。

## 官方与辅助来源

- [ETHOnline 2026 提交详情](https://ethglobal.com/events/ethonline2026/info/details)
- [ETHGlobal 活动列表](https://ethglobal.com/events)
- [The Graph ETHOnline 2026 奖项](https://ethglobal.com/events/ethonline2026/prizes/the-graph)
- [ETHGlobal Rules & Code of Conduct](https://ethglobal.com/rules)
- [Aave Health Factor 与清算说明](https://aave.com/help/borrowing/liquidations)
- [公开 Aave V3 清算记录](https://defi-terminal.com/liquidations)

后两项和 RPC 只用于候选地址预筛与独立对照。比赛资格证据仍必须来自产品实际使用的实时 The Graph 数据。
