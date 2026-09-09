# The Graph 数据源筛选与实时探针

审计时间：2026-09-01，Asia/Shanghai。本文是赛前研究记录，不包含产品接入代码。

## 结论

开赛后的验证顺序应为：

1. **Aave V3 Ethereum 官方 Subgraph**：唯一 P0，承担仓位和清算风险主链路。
2. **Pinax EVM Substreams**：赛内默认不做；只有公开 Web 核心提前完成且事件真正改变报告时才重新评估。
3. **The Graph Token API**：赛内默认不做；通用余额会稀释 Aave 风险叙事。
4. **ENS 官方 Subgraph**：保留研究，不进入默认实现；简单名称解析不满足当前 ENSv2 奖项。
5. 其他 Aave 社区部署：只作故障备选，不能因为查询量高就直接替换官方部署。

最小可提交产品只需要完成第 1 项。第 2–4 项都必须通过 milestone gate，不能拖累 Aave 风险闭环。

## 赛道适配判断

[The Graph 的 ETHOnline 2026 奖项页](https://ethglobal.com/events/ethonline2026/prizes/the-graph) 对 AI Continuity 的资格要求明确写出：The Graph 必须是 load-bearing，实时数据应来自 Subgraphs、Subgraph MCP 或 Substreams，且产品必须对数据进行推理、决策、自动化或自然语言交互。

因此：

- Aave Subgraph + 风险计算 + AI 解释，足以构成 AI Continuity 的正确核心。
- Aave Subgraph + Pinax Substreams，若两者共同影响结果，可以同时具备申报 composable/standardized track 的理由。
- Token API 虽然属于 The Graph Market 数据服务，但没有在该 AI track 的资格枚举中明确出现，不应作为唯一资格依赖。
- ENS Subgraph 若只做输入美化，不足以证明“组合”价值。

## 候选清单

| 优先级 | 数据源 | 当前标识 | 能支撑的产品能力 | 结论 |
|---|---|---|---|---|
| P0 | Aave V3 Ethereum 官方 Subgraph | `Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g` | 用户储备、借贷、抵押、交易、储备参数、风险计算 | 采用 |
| 不计划 | ENS 官方 Subgraph | `5XqPmWe6gjyrJtFn9cLy237i4cWw2j9HcUJEXsP5qGtH` | ENS → 地址和反向名称 | 与 ENSv2 奖项不匹配 |
| 不计划 | Pinax EVM Substreams | `pinax-network/substreams-evm` | ERC-20/native transfer、Approval、实时流和游标 | 核心提前完成后才重审 |
| 不计划 | The Graph Token API | `/v1/evm/balances`、`/v1/evm/transfers` | 通用余额、转账、价格与历史 | 保留研究，不进入默认 backlog |
| 备选 | Aave V3 Ethereum 社区部署 | `JCNWRypm7FYwV8fx5HhzZPSFaMxgkPuw4TnR3Gpi81zk` | Aave 仓位数据 | 官方部署失败后再核验 |
| 备选网络 | Aave V3 Base 官方 Subgraph | `GQFbb95cE6d8mV989mL5figjaGaKCQB3xqYrr1bRyXqF` | Base 上的 Aave 仓位 | 不与 Ethereum 同时首发 |

## P0：Aave V3 Ethereum 官方 Subgraph

### 选择依据

- Aave 官方 [`protocol-subgraphs`](https://github.com/aave/protocol-subgraphs) 仓库把该 ID 列为 `ETH Mainnet V3` 的 active deployment。
- Graph Explorer 显示网络为 Ethereum mainnet、版本 `v0.0.6`、约 13.8K GRT signal。
- 当前部署 Schema 包含 `Reserve`、`UserReserve`、用户交易、余额历史和清算事件。
- `UserReserve` 提供 `currentATokenBalance`、`currentVariableDebt`、`currentStableDebt` 与 `usageAsCollateralEnabledOnUser`。
- `Reserve` 提供价格关系、decimals、LTV、liquidation threshold、liquidity/borrow indices 等风险计算输入。

### 重要限制

Aave 官方文档明确说明，Subgraph 中会计息的 aToken 和 debt token 数值是索引时快照，不能直接当作查询时余额。比赛实现必须使用 Aave 的格式化逻辑或经过验证的等价计算，把 index、rate 和时间因素纳入；否则健康因子会与 Aave 前端不一致。

### 开赛日最小探针

使用一个确定存在 Aave V3 仓位的公开测试地址，依次验证：

1. `_meta` 返回最新 block 且 `hasIndexingErrors=false`。
2. `userReserves(where: { user: <lowercase address> })` 返回非空。
3. 返回的供应、债务、抵押开关、资产 decimals、价格和清算阈值足以重建用户摘要。
4. `userTransactions` 能按时间倒序返回最近活动。
5. 相同地址的计算结果与 Aave 官方前端在可解释误差范围内一致。

只有第 1–5 项全部通过，才开始风险引擎实现。

## 不计划：ENS 官方 Subgraph

Graph Explorer 当前显示：Ethereum mainnet、版本 `v1.1.0`、约 76.1K GRT signal。它适合把 Web 表单中的 `vitalik.eth` 解析为地址，并在报告中展示反向名称。

它可以改善地址输入，但 ETHOnline 2026 ENS 奖项要求 ENSv2 Sepolia 在产品中承担核心能力。仅增加 mainnet 名称解析既会占用时间，也不能形成合格的 Prize Magnet 集成，因此比赛默认不做。若赛后加入，ENS 查询错误仍不得阻断原始地址流程。

## P1.5：Pinax EVM Substreams

[`pinax-network/substreams-evm`](https://github.com/pinax-network/substreams-evm) 是当前维护中的仓库；旧的 `substreams-evm-tokens` 已归档并指向它。当前仓库说明：

- ERC-20 `transfers` 模块包含 `Transfer` 和 `Approval` 事件。
- native 模块包含 ETH 转账与余额变化。
- 聚合包可输出至 ClickHouse 或 Postgres；仓库也提供预构建 `.spkg`。
- Ethereum、Base、BSC、Polygon、Arbitrum、Optimism、Avalanche 等 EVM 网络受支持。

若赛后重新评估，它唯一合理的用途是使用 Substreams 事件触发新的 Aave 快照并形成可核验事件时间线：

```text
Substreams event -> address filter -> Aave snapshot refresh
                 -> deterministic risk delta -> web event timeline
```

启用门槛：

- 公开 Web 核心已部署、可复现且无 P0/P1。
- 能直接消费一个已发布 package，不在比赛中从零建设完整 Rust pipeline。
- 断线重连、cursor 和重复事件行为已测试。
- Approval 事件确实进入风险规则，而不是只显示原始日志。

## P2：Token API

[The Graph Market 文档](https://thegraph.com/docs/en/substreams/providers/the-graph-market/) 显示 Token API 提供多链实时和历史 balances、transfers、holders 与 DEX swaps，并使用 The Graph Market API token 鉴权。

2026-09-01 的无凭据探针结果：

| 探针 | 结果 |
|---|---|
| `GET https://api.pinax.network/v1/health` | HTTP 200，`{"status":"OK"}` |
| `GET https://api.pinax.network/v1/networks` | HTTP 200 |
| Ethereum balances 索引位置 | block `25882474`，`2026-09-01 12:36:59 UTC` |
| Ethereum transfers 索引位置 | block `25882475`，`2026-09-01 12:37:11 UTC` |
| 用官方示例真实地址请求 `/v1/evm/balances` | HTTP 401，无 token 不返回钱包数据 |
| 请求 `/v1/evm/transfers` | HTTP 401，无 token 不返回钱包数据 |

这证明服务和实时索引状态存在，但没有完成经过鉴权的真实钱包数据验收。不要把 HTTP 200 的 `/networks` 当成产品链路已通过。

Token API 的合理用途是补充非 Aave 资产集中度和普通钱包活动。如果时间紧，应完全删掉它，保持“专注 Aave 清算风险”的叙事。

## 已执行的网关探针

### Subgraph Network Gateway

对 Aave V3 Ethereum 官方 Subgraph 发送 `_meta` 查询：

- `gateway.thegraph.com/api/subgraphs/id/...`：返回 `auth error: missing authorization header`。
- `gateway-arbitrum.network.thegraph.com/api/subgraphs/id/...`：同样要求 Authorization。
- 旧 Hosted Service `api.thegraph.com/subgraphs/name/...`：HTTP 301 跳转到错误页，不能使用。
- x402 endpoint：HTTP 402 并返回支付要求，证明该 Subgraph 路由可被网关识别；赛前未授权任何支付，因此没有继续。

结论：当前缺少 Subgraph Studio API key，无法诚实声称已经完成真实地址的 live GraphQL 返回验证。开赛后创建 key 是第一个外部依赖动作。

### Schema 与维护状态

虽然没有使用凭据查询数据，仍已完成以下只读核验：

- Graph Explorer 当前部署页面可访问，并公开当前部署 Schema。
- Aave 官方仓库在 2026-08-10 仍有提交。
- Pinax Substreams EVM 仓库在 2026-07-09 仍有提交。
- ENS Subgraph 仓库在 2026-06-29 仍有提交。

这些只证明项目仍有维护信号，不等价于具体查询已通过。

## 开赛后 30 分钟决策表

| 时间 | 必须得到的证据 | 失败时动作 |
|---|---|---|
| 0–5 分钟 | 创建受限、低额度的 Studio API key | 记录平台故障，尝试官方 workshop/support |
| 5–10 分钟 | Aave `_meta` 新鲜且无 indexing error | 尝试官方部署的其他当前版本或社区备选 |
| 10–20 分钟 | 一个真实 Aave 用户的 `userReserves` 非空 | 更换经过公开验证的测试地址；检查大小写和 market |
| 20–30 分钟 | 本地健康因子与 Aave 前端接近 | 缩小规则，只展示可验证仓位事实，不发布错误健康因子 |

30 分钟后仍无法完成 Aave 证据闭环，就暂停 Web 界面和所有可选数据源，先解决 Subgraph。不得用 RPC、Etherscan 或静态 fixture 冒充正式 Graph 主链路。

## 最终推荐范围

### 安全提交范围

- Ethereum mainnet。
- Aave V3 官方 Subgraph。
- 无账号地址表单、实时分析和可重新打开的报告页面。
- Aave 仓位、健康因子、债务/抵押构成。
- 确定性风险结果 + AI 证据解释。

### Sponsor 扩展范围

The Graph 核心完成后，默认顺序改为 Uniswap 去杠杆预览，再到 Bazantic agent gateway/recipe。它们不是 Graph 数据源，具体资格与 Gate 见 [13-prize-magnet-selection.md](13-prize-magnet-selection.md)。

ENS、Substreams 和 Token API 不属于默认 stretch；只有官方奖项变化或重新通过胜率审计时才允许进入 backlog。

不要首发多链。若 Ethereum 官方部署不可用，可整体切换到 Base，但不能同时维护两套未验收路径。
