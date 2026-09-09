# Wallet Vitals 竞品与差异化定位

审计时间：2026-09-01，Asia/Shanghai。以下能力来自各产品公开页面的当日表述，不代表已完成注册、付费或端到端产品测试。

## 结论

“Aave health factor + 仪表盘/提醒 + AI 解释”已经是拥挤的功能组合，不能单独成为 Wallet Vitals 的原创性叙事。

Wallet Vitals 的差异化核心应当是：

> 用可复核的 The Graph 快照说明当前风险、前后发生了什么变化，以及在明确压力假设下什么阈值会被突破。AI 只解释计算结果，不生成风险数字。

这个定位把产品从“又一个阈值报警 Bot”缩成“带来源凭证的仓位变化与压力解释器”。在核心通过 Gate 后，再用 Uniswap 把风险边界转成无签名的去杠杆预览，并用 Bazantic 让代理调用同一工作流；二者都不改变风险事实来源。

## 直接竞品

| 产品 | 公开页面宣称的能力 | 与 Wallet Vitals 的重合 | 不参与的竞争 |
|---|---|---|---|
| InRange | Aave V3 多链仓位、health factor、Telegram 提醒、Claude AI 问答 | 仓位、AI、Telegram 几乎全部重合 | 不在比赛内追求多链仪表盘或通用问答 |
| AaveGuard | 实时 health factor/LTV、自定义危险区规则、历史信号、Telegram 通知 | 阈值监控与提醒重合 | 不建设复杂规则配置界面 |
| Ava Protocol | Telegram 风险提醒、钱包风险、补仓方案模拟与用户确认后执行 | 风险说明和情景模拟重合 | 不准备交易、补仓或签名路径 |
| MorphoRisk | Aave/Morpho health factor 跟踪、Telegram 阈值提醒和付费订阅 | Telegram 清算提醒直接重合 | 不在比赛内做支付和订阅 |
| Alertio | Aave V3/V4 health factor 阈值、Telegram/邮件/webhook 提醒 | 健康因子告警重合 | 不做通用告警平台 |

## 三个差异化核心

### 1. Risk Delta

产品不只显示“现在 health factor 是 1.18”，还对比两份可比的 Graph 快照，列出：

- 总抵押、总债务和 health factor 变化。
- 按资产的 supply/debt 变化。
- collateral enabled 等状态变化。
- 前后快照各自的 block/time 和 evidence refs。

它只声称“观察到的变化”。若没有可验证事件，不把变化自动归因为价格下跌、用户交易或利息累积。

### 2. Stress Ladder

用同一个确定性 health factor 核心重算三个固定情景：抵押资产 USD 价格统一下调 5%、10%、20%，债务价值不变，其余参数保持快照值。

该能力用来回答“在这个保守情景下，哪个阈值会被突破”。它不是价格预测、不预计清算时间，也不声称某个 health factor 对所有仓位都“安全”。Aave 官方也指出不存在适用于所有仓位的统一安全健康因子。

同一数学核心再给出 Liquidation Buffer：在统一抵押价格下跌、债务价值不变的限制下，计算 health factor 恰好降至 1 的理论冲击幅度。它把离散的三档压力测试变成一句更容易记住的话，同时必须完整显示假设。产品不再制造缺少校准依据的 0–100 综合风险分数。

### 3. Evidence Receipt

每份报告携带：

- Graph provider 和 deployment。
- network、source block/time 和 queried at。
- rules version 和 stress assumptions。
- 触发规则与 evidence refs。
- 数据缺失、indexing error 或陈旧状态。

Graph 失败、数据过旧或快照不可比时，系统明确停止对应结论，不用 RPC 或旧缓存静默补位。

## 产品取舍

### 比赛内必做

- 单网络 Ethereum、单协议 Aave V3。
- 实时 The Graph 仓位与来源元数据。
- 当前风险、Risk Delta、Stress Ladder 和 Evidence Receipt。
- Liquidation Buffer，以及一次基于本次证据的引导式 AI 追问。
- AI 只解释结构化计算结果，且有确定性 fallback。
- 无需账号、无需钱包连接的地址输入与 Web 报告端到端体验。

### 通过核心 Gate 后的 Sponsor 扩展

- Uniswap De-risking Preview：根据目标 health factor 和真实路线，展示所需 collateral-to-debt 转换、价格影响和报价时间；不签名、不执行。
- Bazantic agent gateway + Recipe：让代理复用同一个地址分析、证据核验和预览流程；普通 Web 不依赖该通道。

### 允许砍掉

- 报告永久链接；必要时只保留有保留期的匿名 `report_id`。
- Bazantic，随后是 Uniswap；它们是最先删除的 Partner Prize 扩展。
- ENS、Substreams、Token API 和多链。
- 按资产的精细 Risk Delta，必要时只保留总抵押、总债务和 health factor 变化。
- 仪表盘、交易执行、自动补仓、支付和 SaaS 后台。

## 评委叙事

建议英文一句话：

> An accountless, evidence-grounded Aave risk copilot that explains what changed, what breaks first, and how to verify it using live The Graph data.

建议三句演示逻辑：

1. Most bots tell you the current health factor; Wallet Vitals shows what changed between verifiable Graph snapshots.
2. It runs transparent collateral-shock scenarios with deterministic math instead of asking an AI to invent risk numbers.
3. Every result carries an evidence receipt, and the analysis stops when Graph data is stale or unavailable.

演示的记忆顺序固定为：what changed、what breaks first、how to verify。详细胜率取舍见 [11-win-rate-audit.md](11-win-rate-audit.md)。

不要声称“市场上没有其他 Aave 风险产品”。正确说法是，Wallet Vitals 把重点放在零账号访问、快照变化、透明压力假设、来源凭证和失败时的诚实停止。

## 来源

- [InRange Aave Dashboard](https://inrange.ai/aave-dashboard)
- [AaveGuard](https://aaveguard.com/)
- [Ava Protocol Aave Position Protection](https://avaprotocol.org/protect/aave-position)
- [MorphoRisk](https://morphorisk.com/)
- [Alertio Aave Health Factor Alerts](https://www.alertio.io/alerts/aave-health-factor)
- [Aave Health Factor & Liquidations](https://aave.com/help/borrowing/liquidations)
- [ETHOnline 2026 judging criteria](https://ethglobal.com/events/ethonline2026/info/details)
