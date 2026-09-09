# Wallet Vitals — Prize Magnet 奖项组合

审计时间：2026-09-02，Asia/Shanghai。本文按 ETHOnline 2026 当日官方奖项页面重新选择项目与最多三个 Partner Prizes，不包含参赛实现代码。

## 最终结论

仍然只做一个项目：**Wallet Vitals**。不再把它视为“只为 The Graph 做完后再看其他奖项”，而是从一开始把模块边界设计成一个核心产品自然命中三个 Sponsor：

1. **The Graph — Best AI Tooling or AI Use Case with The Graph (Continuity)**：主奖项和不可替代的数据核心。
2. **Uniswap Foundation — Best Uniswap Stack Contribution（优先 Continuity）**：把风险结果转成可复核的去杠杆预览。
3. **Bazantic — Help an Agent Use Your Hackathon Project，并争取同 Sponsor 下的 Recipe 类奖项**：把同一报告 API 变成代理可发现、可调用的服务。

官方提交页说明，一个项目最多选择三个 Partner Prizes；同一 Partner 有多个 track 时，只占一个 Partner Prize 名额，但可同时符合该 Partner 的多个 track。因此这里选择的是三个 Sponsor，不是只选三个子赛道。

## 统一产品故事

> Wallet Vitals discovers Aave liquidation risk from live Graph data, previews a verifiable Uniswap de-risking route, and exposes the same evidence-grounded workflow to agents through Bazantic.

三个 Sponsor 不是三个并列 Logo，而是一条连续用户价值链：

```text
The Graph live Aave position
          |
          v
deterministic risk + Risk Delta + Stress Ladder
          |
          v
Uniswap de-risking preview for the required collateral-to-debt conversion
          |
          v
Bazantic gateway + recipe lets an agent run the same workflow
```

公开 Web 对人类用户仍然无需账号、无需连接钱包、无需签名。Uniswap 部分只生成实时、可核验的去杠杆预览，不执行交易。Bazantic 仅为单独的 agent/API 通道提供 gateway 和 recipe，不把普通 Web 用户放进登录或支付路径。

## 选择方法

使用五个方向性维度，而不是伪造精确获奖概率：

- 核心适配度 35%：Sponsor 是否天然参与主要用户结果。
- 增量成本 25%：5 分代表在核心完成后改动较小。
- 奖项结构 15%：是否有多个获奖名额、qualifying/split 或同 Sponsor 多 track。
- 规则确定性 10%：资格要求是否已经完整公布并可验收。
- 叙事一致性 15%：是否强化“发现风险、说明边界、给出可核验下一步”。

分数只用于排序，不是官方评分或获奖概率。

## 先反推项目，而不是只筛 Sponsor

按同一标准比较五个可行的单人项目概念后，Wallet Vitals 仍然胜出。它不是因为已经投入研究就被保留，而是因为它能复用一个数据模型、一个风险核心、一个 Web/API 和一个 Demo，同时命中三项。

| 项目概念 | Sponsor 组合 | 技术重叠 | 单人可完成性 | Demo 一致性 | 结论 |
|---|---|---:|---:|---:|---|
| Wallet Vitals 风险到行动代理 | The Graph + Uniswap + Bazantic | 5.0 | 4.5 | 5.0 | 选择 |
| Human-backed payment agent | World + Arc + Bazantic | 4.0 | 2.0 | 4.0 | World Sandbox、Arc 钱包与支付同时过重 |
| Stablecoin treasury agent | Arc + Privy + Chainlink | 4.5 | 2.0 | 4.0 | Chainlink 规则未公布，且需钱包与资金流 |
| ENSv2 agent directory | ENS + World + Bazantic | 4.0 | 2.5 | 4.0 | ENSv2 合约、World 授权和代理分发形成三套验收 |
| Aqua risk rebalancer | 1inch + The Graph + Bazantic | 4.0 | 2.0 | 4.0 | Aqua/SwapVM 与 onchain execution 显著增加风险 |

Wallet Vitals 还有一个结构优势：The Graph-only 核心本身就是完整、可提交的产品；第二和第三 Sponsor 都是可拔插模块。其他概念的三个 Sponsor 通常互为前置条件，任何一个失败都会让主故事断裂。

| Sponsor | 核心适配 | 增量成本 | 奖项结构 | 规则确定性 | 叙事一致性 | 决策 |
|---|---:|---:|---:|---:|---:|---|
| The Graph | 5.0 | 5.0 | 4.0 | 5.0 | 5.0 | 必选，主链路 |
| Bazantic | 4.5 | 4.0 | 4.0 | 5.0 | 4.5 | 第三奖项，代理分发层 |
| Uniswap Foundation | 4.0 | 3.5 | 4.5 | 5.0 | 4.5 | 第二奖项，风险到行动预览 |
| ENS | 2.0 | 2.0 | 4.0 | 5.0 | 2.0 | 不选；ENSv2 Sepolia 必须居于核心 |
| Arc | 2.5 | 1.0 | 5.0 | 5.0 | 2.5 | 不选；要求钱包、USDC 和 Arc 交易 |
| World | 1.5 | 1.5 | 4.0 | 5.0 | 1.5 | 不选；人类授权不是当前问题 |
| 1inch | 2.5 | 1.5 | 4.0 | 5.0 | 2.5 | 不选；Aqua/SwapVM 与执行要求过重 |
| Privy | 2.0 | 1.5 | 3.0 | 5.0 | 2.0 | 不选；必须创建钱包并完成资金流 |
| Hedera | 1.0 | 1.0 | 4.0 | 5.0 | 1.0 | 不选；会引入第二条链和完整支付系统 |
| Ledger | 待定 | 待定 | 待定 | 1.0 | 待定 | 奖项详情未公布，不预选 |
| Chainlink | 待定 | 待定 | 待定 | 1.0 | 待定 | 奖项详情未公布，不预选 |

## 三个 Sponsor 的资格证明

### 1. The Graph

必须完成：

- 从 Graph provider 查询实时 Aave V3 Ethereum Subgraph。
- The Graph 是 load-bearing；关闭它时核心分析必须停止。
- 对实时数据做确定性风险推理和有证据引用的 AI 解释。
- 公开仓库、清楚 README、2–4 分钟视频和 Continuity 披露。

它是整个项目的 P0。其他两个 Sponsor 不能影响它的正确性、部署和演示。

### 2. Uniswap Foundation

新增 **De-risking Preview**：

- 风险引擎先计算达到目标 health factor 所需减少的债务量。
- 根据用户的抵押与债务资产，向实际使用的 Uniswap 产品请求实时兑换预览。
- 显示输入量、预期输出、路由、价格影响、数据时间和“仅为预览，不执行交易”。
- 计算必须考虑卖出抵押物会同时降低清算加权抵押，不能把简单的债务差额冒充可执行方案。
- 无可用路由、流动性不足或报价失败时明确返回 unavailable，不改用硬编码报价。
- 增加 `FEEDBACK.md`，完成官方 Developer Feedback Form，并在 README 指向相关代码。

公开 Web 仍无钱包连接与签名。该模块的目标是把“什么先失守”延伸成“在当前证据下，要恢复到目标边界需要多大转换”，而不是做交易终端。

### 3. Bazantic

在核心 JSON API 之上增加 agent 通道：

- 为 Wallet Vitals API 创建 Bazantic x402/MPP Gateway。
- 创建 Recipe，明确何时分析地址、如何读取证据、何时请求 Uniswap 去杠杆预览。
- 用相同 prompt、模型、设置和 API access 做 raw API 与 Recipe 的 A/B 测试；保存输入和输出。
- 录制代理从地址到风险报告再到去杠杆预览的完整屏幕流程。
- 若可行，让同一 Recipe 同时使用 Wallet Vitals 服务与 Uniswap Sponsor API，争取 Bazantic 的 Sponsor API Recipe 子赛道。

Bazantic 官方要求参赛者创建账号并在提交中提供用户名。这个是开发者侧的外部依赖；若注册、gateway 或 A/B 证据在 G4 前无法稳定完成，立即放弃 Bazantic，不改动普通 Web 产品。

## 为什么不选 ENS 或 Arc

当前 ENS 奖项不是“解析 `.eth` 就有资格”。主奖要求 ENSv2 Sepolia 成为产品核心，Continuity 奖也要求把 ENSv2 集成进既有项目的测试网部署。Wallet Vitals 的核心是 Ethereum mainnet Aave 风险；为 ENSv2 增加命名空间、权限和 Sepolia 合约会形成第二条产品故事。

Arc 的 agent 赛道要求代理在 Arc 上持有钱包、使用 USDC 自主支付或结算，并使用 Circle Agent Stack。它会同时引入钱包托管、交易、安全和第二条链，明显超过 10–20% 增量，也破坏当前“无签名只读报告”的可信边界。

## 实施 Gate

三个 Sponsor 是目标组合，不是必须同时完成的借口：

1. G0–G2 只允许开发 The Graph + Aave 风险核心。
2. 核心 Web 已公开、数学对照通过且无 P0/P1 后，才开始 Uniswap De-risking Preview。
3. Uniswap 的真实报价、失败状态和测试通过后，才开始 Bazantic gateway/recipe。
4. 任一 Sponsor 未留下真实资格证据，就不在提交表单选择它。
5. 砍项顺序固定为 Bazantic → Uniswap → The Graph 之外的全部 stretch；不牺牲核心换取第三个 Logo。

## 开赛日复核

- 再打开奖项总览，确认 Ledger、Chainlink 或其他页面是否更新。
- 只有新公布奖项在适配度、增量成本和奖项结构上明显超过当前第三名，才允许替换；不能临时增加第四套集成。
- 保存当日官方规则和各 Sponsor 资格文字。
- 记录 Bazantic 注册、Uniswap API access 和 The Graph key 是否可用。

## 官方依据

- [ETHOnline 2026 提交、最多三个 Partner Prizes 与评审规则](https://ethglobal.com/events/ethonline2026/info/details)
- [ETHOnline 2026 奖项总览](https://ethglobal.com/events/ethonline2026/prizes)
- [The Graph 奖项](https://ethglobal.com/events/ethonline2026/prizes/the-graph)
- [Uniswap Foundation 奖项](https://ethglobal.com/events/ethonline2026/prizes/uniswap-foundation)
- [Bazantic 奖项](https://ethglobal.com/events/ethonline2026/prizes/bazantic)
- [ENS 奖项](https://ethglobal.com/events/ethonline2026/prizes/ens)
- [Arc 奖项](https://ethglobal.com/events/ethonline2026/prizes/arc)
