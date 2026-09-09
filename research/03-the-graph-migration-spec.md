# The Graph 替换架构与比赛内 MVP

## 产品一句话

一个无需账号的钱包风险 Web 应用：用户粘贴公开地址后，系统用 The Graph 的实时 Aave 仓位说明当前风险、前后快照发生了什么变化、什么压力边界会先失守，以及如何核验证据，再由 AI 解释已经计算的结果。

## 核心设计约束

1. The Graph 必须是核心依赖。用户可见的活动、仓位和风险事实都来自比赛期间确认的实时 Graph 数据源，不用 mock、静态样本或其他链上 API 代替主链路。
2. 风险结论先计算、后叙述。LLM 不自行猜余额、健康因子或风险等级，只解释结构化证据。
3. 每份报告和 AI 解释都可追溯。输出携带数据源、deployment、block/time、queried at、规则版本、情景假设和 evidence refs。
4. 第一版只做有限而完整的路径，避免同时扩展多链、交易执行、复杂仪表盘和计费。
5. 具体 Subgraph 名称、部署 ID、网络和查询能力必须在开赛后用实时端点验证，本文不预先假定可用性。
6. 产品不要求注册、登录、连接钱包、签名或提供私钥。所有 Graph 与模型密钥只存在服务端。

## 数据源优先级

比赛内的资格主链路锁定为 Aave V3 Ethereum 官方 Subgraph。它负责用户仓位、借贷活动、储备参数和计算健康因子所需的证据。这样即使其他数据源未完成，The Graph 仍然是产品不可替代的核心依赖。

Pinax EVM Substreams 不进入默认计划。只有核心 Web 产品已经公开运行，且 Substreams 事件能真正驱动新的 Aave 快照或事件时间线时才评估；否则在 The Graph Sponsor 内只申报 AI Continuity，不申报 composable/standardized 子赛道。

ENS Subgraph 和 Token API 均不进入默认实现。当前 ENS Partner Prize 要求 ENSv2 Sepolia 成为核心能力，简单名称解析不构成合理参赛集成；Token API 会稀释 Aave 风险叙事。详细数据筛选见 [05-graph-data-source-screening.md](05-graph-data-source-screening.md)，三 Sponsor 选择见 [13-prize-magnet-selection.md](13-prize-magnet-selection.md)。

## 目标架构

```text
Public browser
  address form / report / guided questions
       |
       v
FastAPI Web + JSON API
       |
       +--> Report Store / Snapshot History
       |
       v
Graph Data Gateway
       |
       +--> Wallet activity adapter
       +--> Token/position adapter
       +--> Aave position adapter
       |
       v
Normalized Evidence Snapshot
       |
       v
Deterministic Risk Engine
       |
       +--> current risk + liquidation buffer
       +--> risk delta + stress ladder
       +--> triggered rules + evidence receipt
       v
LLM Narrative Layer
       |
       v
Shareable accountless web report
       |
       +--> optional Uniswap de-risking preview
       |
       +--> optional Bazantic agent gateway + recipe
```

## 保留的产品概念

- 用户输入公开地址并查看当前状态。
- 系统保存可比较的历史快照，说明两次分析之间的变化。
- 用户不需要连接钱包或提供身份信息。

前两项延续上游的钱包登记与轮询概念，但 Web 界面、API、Graph 数据、报告模型和风险能力均是比赛期间的新实现。不能把旧轮询器简单包一层网页或 AI。

## 建议的比赛内 MVP

### 必做用户路径

1. 用户打开公开页面，无需登录或连接钱包。
2. 粘贴 EVM 地址并点击 **Analyze live position**。
3. 服务端从实时 Graph provider 生成当前证据快照，返回确定性风险、Liquidation Buffer、Risk Delta 与 Stress Ladder。
4. 报告同时显示 Evidence Receipt 和 Graph 数据新鲜度；首次查询没有历史时明确显示 `no_baseline`。
5. 页面提供“发生了什么”“什么先失守”“如何核验”三个固定引导问题。AI 只基于当前 `report_id` 的结构化结果回答，并引用 evidence refs。
6. 报告可通过不含密钥的 URL 或 `report_id` 重新打开；任何动态数据都显示生成时间，不冒充持续实时状态。
7. CLI 仅作为评委复现和故障诊断入口，不作为主 Demo；主动提醒、用户账号和个性化通知不做。

The Graph 核心通过全部 Gate 后，才允许加入 Uniswap 去杠杆预览和 Bazantic agent 通道；二者失败都不能改变或降级核心风险报告。

### Partner Prize 扩展边界

- Uniswap adapter 接受经过验证的仓位和目标 health factor，只返回实时转换预览与来源元数据，不持有私钥、不签名、不广播交易。
- 去杠杆数学必须同时考虑卖出抵押物和偿还债务对 health factor 的影响；无路由或流动性不足时返回 `unavailable`。
- Bazantic gateway 只包裹现有 JSON API；Recipe 组织“分析风险 → 请求去杠杆预览”的同一工作流，不创建第二套风险逻辑。
- 普通 Web 用户仍无需 Bazantic 账号或 x402 支付。开发者侧 gateway 不得成为核心报告的前置条件。

### 第一版风险信号

优先选择能由比赛期间验证的数据源完整支持的信号：

| 信号 | 确定性计算 | 最低证据 |
|---|---|---|
| Aave 清算风险 | 按健康因子分级 | 当前 health factor、债务、抵押物、数据位置 |
| Liquidation Buffer | 在统一抵押价格冲击、债务价值不变的假设下，计算使 health factor 降至 1 的理论冲击幅度 | 当前 health factor、完整情景假设、数据完整性状态 |
| Risk Delta | 对比可比快照的抵押、债务、健康因子和抵押开关 | 前后快照、各自的 block/time 和 evidence refs |
| Stress Ladder | 在抵押资产价格统一下调 5%、10%、20%、债务价值不变的保守假设下重算 health factor | 当前仓位、储备价格、清算阈值、情景假设 |

如果某个信号缺少可靠 Graph 数据，系统应标为 `unsupported`，不能用估算值补齐。

## 模块契约

### Graph Data Gateway

职责：统一 GraphQL 请求、分页、超时、重试、速率限制、查询版本和数据源标识。

建议输出：

```json
{
  "source": {
    "provider": "the-graph",
    "deployment": "verified-at-kickoff",
    "network": "ethereum",
    "block_number": 0,
    "queried_at": "RFC3339"
  },
  "records": [],
  "warnings": []
}
```

### Normalized Evidence Snapshot

职责：把不同 Subgraph 的字段转换为稳定的内部模型；保留原始来源坐标，不让风险引擎依赖供应商字段名。

必需字段：钱包、网络、资产或协议、数值、单位、区块/时间、数据源、完整性警告。

### Deterministic Risk Engine

职责：纯函数式计算协议原生指标、派生指标、确定性等级与规则；同一证据和规则版本必须得到相同结果。MVP 不生成缺少校准依据的 0–100 综合分数。LLM 不参与数值计算。

建议输出：

```json
{
  "level": "high",
  "health_factor": "1.14",
  "liquidation_buffer": "0.1228",
  "rules_version": "v1",
  "triggers": [
    {
      "rule": "aave_health_factor",
      "severity": "high",
      "observed": "1.14",
      "threshold": "< 1.20",
      "evidence_refs": ["evidence:1"]
    }
  ]
}
```

### Risk Delta

只比较同一钱包、network、market、deployment 和 schema 版本下，block 严格递增的两份完整快照。输出总抵押、总债务、health factor、按资产的 supply/debt 和抵押开关变化。如果没有前序快照或快照不可比，返回 `no_baseline` 或 `incomparable`。

Risk Delta 说明“观察到什么变化”。除非另有可验证事件证据，不能声称变化由某个用户动作或价格事件导致。

### Stress Ladder

第一版只支持三个固定保守情景：所有抵押资产的 USD 价格同时下调 5%、10% 和 20%，债务资产 USD 价值保持不变，其余 Aave 参数保持快照值。这是敏感性压力测试，不是价格预测、清算时间预测或投资建议。

输出每个情景的重算 health factor、是否跨过规则阈值、完整假设和 evidence refs。零债务、缺价格、不支持的 eMode 或不完整数据必须返回明确状态，不生成伪精确数字。

### Liquidation Buffer

在 Stress Ladder 的同一组限制下，若当前 health factor 为有限值且大于 1，则统一抵押价格下跌到 health factor 等于 1 的理论幅度为 `1 - 1 / health_factor`。例如 health factor 为 1.20 时，理论缓冲约为 16.7%。

该指标只在债务价值不变、所有抵押资产同比例重估、清算参数不变且证据完整时显示。它是静态敏感性指标，不是安全保证、价格预测、清算时间或操作建议。health factor 小于等于 1、零债务或不完整状态必须返回明确状态，不显示误导性百分比。

### Evidence Receipt

每份报告最少列出 provider、deployment、network、source block/time、queried at、rules version、scenario assumptions 和 evidence refs。`Evidence Receipt` 是来源与可复核性摘要，不宣称是密码学证明、审计证书或风险担保。

### LLM Narrative Layer

职责：把已计算的事实变成短报告，解释“发生了什么、为什么重要、用户可以检查什么”。它必须引用 `evidence_refs`，遇到缺失数据必须明确说明，禁止生成交易执行指令或虚构收益/风险数字。

### Accountless Web Boundary

Web 层只负责地址输入、加载状态、报告分区、三个固定引导问题和来源展开。浏览器不接触 Graph key 或模型 key，不请求钱包连接，不使用第三方登录。服务端为匿名请求设置并发上限、地址冷却时间和报告保留期，避免公开 Demo 耗尽额度；不持久化原始 IP。

## 非目标

- 自动签名、托管或执行交易。
- 覆盖所有 EVM 链和所有 DeFi 协议。
- 用 AI 代替风险规则。
- 在主链路完成前建设复杂仪表盘、订阅计费或增长系统。
- 为了“多产品”而接入不影响用户结果的 Graph 功能。
- 用户账号、OAuth、Telegram、Discord、邮件或推送通知。
- React/Next.js 构建链；第一版使用服务端模板、静态 CSS 和极少量浏览器 JavaScript。

## The Graph 验证门槛

开赛后，每个候选数据源都必须通过以下探针：

- 公共或团队可复现的实时查询成功。
- 返回目标钱包的非静态数据，且能记录 block/time 元数据。
- 字段足以计算对应风险信号。
- 查询分页、空结果和限流行为已知。
- README 写明部署/数据源、查询用途和故障降级方式。

只有通过探针的数据源才进入 MVP。官方要求参考 [The Graph 奖项页面](https://ethglobal.com/events/ethonline2026/prizes/the-graph)。
