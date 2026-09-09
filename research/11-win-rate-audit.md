# Wallet Vitals 胜率审计与优化决策

审计时间：2026-09-01，Asia/Shanghai。本文只调整赛前规格、实施顺序和演示策略，不包含参赛代码或产品资产。

## 结论

无账号 Web 迁移的最终产品、路由、安全和失败边界见 [12-accountless-web-pivot.md](./12-accountless-web-pivot.md)。

当前方案已经能满足 The Graph AI Continuity 的基本资格。2026-09-02 的官方奖项复核进一步把项目设计成一个 Prize Magnet：The Graph 是核心事实层，Uniswap 是无签名的去杠杆预览，Bazantic 是代理分发层。主要风险变成：Sponsor 扩展抢占核心时间、AI 容易被看成文案层，以及公开匿名请求可能耗尽服务额度。

本轮确定五项优化：

1. 删除缺少校准依据的 0–100 综合风险分数，保留 Aave health factor、确定性等级和可复核规则。
2. 在 Stress Ladder 上增加 Liquidation Buffer，回答“在限定假设下，抵押价格还可承受多大统一跌幅才到 health factor 1”。
3. 把 Risk Delta 前移到 Web 视觉完善之前，把 AI 与公开部署放在任何 Sponsor 扩展之前。
4. AI 除了生成短摘要，还要回答一次有 evidence refs 的引导追问，优先展示“发生了什么”“什么先失守”“如何核验”。
5. Demo 主动展示 Graph 失败时停止分析，用十秒以内证明 The Graph 是 load-bearing，而不只靠口头声称。

## 对官方评审维度的判断

以下为基于现有规格的主观审计，不是官方分数，也不代表获奖概率。官方没有公开各维度权重。

| 维度 | 当前判断 | 主要缺口 | 优化后的证据 |
|---|---|---|---|
| Technicality | 强 | Aave 数学很深，但可能被实现风险拖垮 | 固定精度数学、真实对照、Delta、Buffer、错误矩阵 |
| Originality | 中上 | Aave 风险仪表盘和提醒已有大量竞品 | accountless access + what changed + what breaks first + how to verify |
| Practicality | 中上 | 部署与复现排得偏晚 | Day 7 前完成无需账号的公开核心 |
| Usability | 中 | 报告信息密度高，AI 只是单向摘要 | 三个引导问题、单屏分层消息、明确失败状态 |
| WOW Factor | 中上 | Evidence Receipt 理性但不够瞬时 | Liquidation Buffer + Graph failure proof |
| The Graph fit | 强 | AI 可能看起来可替换，load-bearing 只靠说明 | 实时 metadata、证据引用、断开 Graph 即停止 |

## 新的评委记忆结构

演示只要求评委记住三个问题：

1. **What changed?** Risk Delta 比较两份可比 Graph 快照。
2. **What breaks first?** Liquidation Buffer 和 Stress Ladder 给出透明的敏感性边界。
3. **How can I verify it?** Evidence Receipt 指向 deployment、block/time、规则版本与 evidence refs。

AI 的作用是把这三组结构化结果按用户问题重新组织并引用证据。它不修改数值、不补齐缺失数据、不猜测变化原因。

## Liquidation Buffer 的边界

在全部抵押资产 USD 价格同比例变化、债务 USD 价值不变、清算阈值与协议参数不变的静态情景中：

```text
liquidation_buffer = 1 - 1 / current_health_factor
```

仅当 health factor 为有限值且大于 1、债务非零、价格和抵押证据完整时显示。结果必须与 Stress Ladder 共用同一个 health factor 核心。它不表示实际安全垫，不预测市场路径，也不考虑清算人、滑点、相关性变化或参数更新。

## 实施优先级调整

旧顺序把 Risk Delta 放在 Day 6、AI 放在 Day 7、部署放在 Day 8。新顺序为：

1. Graph 实时资格与 schema。
2. Aave 归一化和经过对照的 health factor 核心。
3. Stress Ladder、Liquidation Buffer、快照存储与 Risk Delta。
4. 无账号 Web 首页、分析 API、报告页与来源展开。
5. AI 摘要与一次引导追问。
6. 部署、可靠性、安全、README 和干净环境复现。
7. 只有核心已公开运行后，才按 Uniswap → Bazantic 的 Gate 顺序扩展；ENS 和 Arc 不进入默认计划。

这让差异化、AI 资格和实际可用性都在第二、第三 Sponsor 之前完成。

## Prize Magnet 组合

默认 Partner Prize 选择为：

1. The Graph AI Continuity，核心且不可删除。
2. Uniswap Foundation Continuity，用实时 De-risking Preview 把风险报告延伸到可核验下一步。
3. Bazantic Continuity，并在真实串联 Sponsor API 时争取其 Recipe 子赛道。

ENS 当前要求 ENSv2 Sepolia 成为核心能力；Arc agent track 要求钱包、USDC 和真实交易。它们都会创造第二条产品主线，因此不选。完整评分和资格证明见 [13-prize-magnet-selection.md](13-prize-magnet-selection.md)。

## Demo 优化

主视频仍控制在 2–4 分钟，但核心画面改为：

- 第一屏直接显示 health factor、Liquidation Buffer 和当前等级，不显示自造综合分数。
- 第二屏显示 Risk Delta，再点一次“什么先失守”引导问题，让 AI 引用 Buffer、Stress Ladder 和 evidence refs 回答。
- 第三屏展开 Evidence Receipt。
- 用预先设计的安全开关让 Graph 请求失败一次，Web 页面明确显示分析已停止；随后恢复正常环境。画面不暴露 key。
- Git 历史和 Continuity 披露保留，但压缩在 15 秒以内，不抢产品主路径时间。

## 不建议做的“优化”

- 不为了凑满三个 Partner Prizes 接入 ENS、Arc、Chainlink、Privy 或其他装饰性依赖；Uniswap 和 Bazantic 也必须通过独立 Gate。
- 不追 Composable/Standardized 赛道，除非 Substreams 真正触发 Aave 快照与用户结果。
- 不增加 React dashboard、多链、交易执行、自动补仓、订阅支付或复杂 agent framework。
- 不提前创建参赛仓库、Bot、设计成品或实现文件。
- 不用 mock 风险钱包、伪造变化或预写 Graph 返回制造演示效果。

## 胜率门槛

在提交前，以下五项缺一项就停止做 stretch：

1. 真实 Graph provider 返回新鲜 Aave 数据和 metadata。
2. health factor、Stress Ladder 与 Liquidation Buffer 共用一个通过真实对照的数学核心。
3. Risk Delta 至少展示一次真实、可比、block 递增的快照变化。
4. AI 回答至少一个用户问题，并对重要判断引用 evidence refs。
5. 公开运行的无账号 Web 路径与干净 checkout 均可复现，Graph 失效时明确停止。

## 官方依据

- [ETHOnline 2026 评审、Continuity 与视频规则](https://ethglobal.com/events/ethonline2026/info/details)
- [The Graph ETHOnline 2026 奖项与 Continuity 资格](https://ethglobal.com/events/ethonline2026/prizes/the-graph)
- [Prize Magnet 三 Sponsor 选择](13-prize-magnet-selection.md)
