# ETHOnline 2026 技术栈与实施 Backlog

适用时间：2026-09-04 至 2026-09-13 12:00 EDT（北京时间 2026-09-14 00:00）。本文是赛前实施规格，不包含参赛代码。

ETHGlobal 活动列表仍把 ETHOnline 2026 标为 9 月 4–16 日，但官方提交详情页当前给出的硬截止时间更早。所有 gate 按 9 月 13 日 12:00 EDT 倒排，9 月 16 日不得作为备用提交日。

## 最终技术决策

继续使用 Python，把上游的钱包跟踪与快照比较概念重构成无需账号的公开 Web 应用。比赛版本是一个单进程异步 FastAPI 服务，使用服务端模板、静态 CSS 和少量原生 JavaScript；不建设 React SPA、登录系统或钱包连接。

### 运行栈

| 层 | 决策 | 理由 |
|---|---|---|
| Python | 3.12 | 已用于上游审计；成熟且避开刚发布解释器的兼容风险。 |
| 包管理 | `uv` + `pyproject.toml` + 提交 `uv.lock` | 安装快，锁文件可复现；CI 使用 `--locked`。 |
| Web/API | `fastapi[standard]` 0.141.1 | 同一进程提供 HTML、JSON API、表单验证、OpenAPI 和 Uvicorn；版本在开赛日重新安装验证。 |
| 页面 | Jinja2 + StaticFiles + 原生 CSS/JS | 无 Node 构建链；服务端密钥不会下发到浏览器。 |
| HTTP/GraphQL | `httpx` 0.28.1 | 一个共享 AsyncClient，统一连接池、超时和鉴权；不引入 GraphQL 框架。 |
| 模型校验 | `pydantic` 2.13.5 + `pydantic-settings` 2.15.0 | 严格验证 Graph 响应、证据模型和环境配置。 |
| 地址处理 | `eth-utils` 6.0.0 | 地址合法性、checksum 和规范化；不为此引入 Web3.py。 |
| 存储 | SQLite + `aiosqlite` 0.22.1 | 单 worker 足够；固定表名、显式 SQL 和 schema version。 |
| 测试 | `pytest` 9.1.1 + `pytest-asyncio` 1.4.0 | 单元、契约和异步集成测试。 |
| 质量 | Ruff，版本由开赛日 lockfile 固定 | 一个工具完成 lint 和 format。 |
| 部署 | 单容器、单副本、持久化 volume | 公开 HTTPS URL、SQLite 持久化和单进程写入语义；平台在开赛后按可用账户选择。 |

以上版本是 2026-09-01 的候选锁定值。开赛日必须在 Python 3.12 干净环境安装并运行最小测试后再生成 lockfile；不能把“当前 PyPI 版本”当成“已兼容验证”。

### 不采用的组件

- Django、React、Next.js 或独立前后端两套工程。
- Telegram、Discord、OAuth、用户账号、钱包连接、签名和交易广播；Uniswap 只提供服务端报价预览。
- SQLAlchemy、Alembic、Postgres 和 Redis。
- Web3.py 或 RPC 作为正式数据主链路。
- Apollo、gql、GraphQL code generator。
- LangChain、CrewAI 或其他 agent framework。
- `@aave/math-utils` Node sidecar。Aave 已在 2026 年归档 `aave-utilities` 仓库。
- 水平扩容、消息队列、定时通知和后台任务集群。
- 复杂仪表盘、登录、计费和 SaaS 多租户后台。

这些不是永远不做，而是不能占用比赛核心路径。

## 依赖边界

应用依赖方向固定为：

```text
web routes / JSON API / CLI
    |
    v
application services
    |
    +--> graph ports ------> HTTP Graph adapters
    +--> storage ports ----> SQLite adapters
    +--> narrator port ----> one hosted LLM adapter
    |
    v
domain evidence + pure risk engine
```

规则：

1. `domain` 不 import FastAPI、HTTP、SQLite 或 LLM SDK。
2. 风险引擎输入只接受验证后的 Evidence Snapshot，输出只包含协议指标、派生指标、确定性等级、规则和 evidence refs；MVP 不生成缺少校准依据的 0–100 综合分数。
3. LLM adapter 不访问 Graph，不计算数值，不写数据库。
4. Web route 只验证请求、调用 application service、选择模板或序列化 JSON。
5. HTML、JSON API 与 CLI 必须复用同一条分析服务，不能形成三套风险逻辑。
6. Graph 不可用时返回显式 degraded/error；禁止自动改用 RPC 或 Etherscan。

## 建议包结构

比赛开赛后再创建以下结构：

```text
src/wallet_vitals/
  app.py
  config.py
  domain/
    evidence.py
    risk.py
  graph/
    client.py
    aave.py
    queries/
  risk/
    aave_math.py
    delta.py
    engine.py
    stress.py
  storage/
    sqlite.py
    schema.sql
  web/
    routes.py
    schemas.py
    templates/
    static/
  cli.py
  ai/
    narrator.py
  integrations/
    uniswap.py
tests/
  unit/
  contract/
  integration/
```

目录表达职责，不要求为了“架构漂亮”创建空文件。没有第二个实现时，不额外建立抽象工厂或插件系统。

## 数据库最小模型

只保留三张固定表：

| 表 | 作用 | 关键约束 |
|---|---|---|
| `risk_snapshots` | 最近证据和风险结果 | 保存 source block/time、规则版本和摘要 JSON |
| `reports` | 可重新打开的匿名报告 | 不可预测 `report_id`、address、snapshot refs、创建与过期时间 |
| `schema_meta` | schema version | 启动时只做已知版本迁移 |

地址以 lowercase 作为查询和索引键，另存 checksum 形式用于显示。报告只包含公开链上数据，不保存账号、钱包连接、原始 IP 或个人资料；过期报告按明确保留期清理。禁止按 network 创建动态表名。

## Aave 数学实现原则

Aave 是全项目最高风险模块，应独立完成并优先验收。

- 以 Subgraph 返回的 scaled balance、principal debt、reserve index、rate、timestamp、price 和 liquidation threshold 构建不可变快照。
- 使用 Python integer/Decimal 实现 WAD、RAY、指数和利息计算；关键路径禁止 binary float。
- 数学公式根据 Aave V3 协议定义重新实现，并在代码注释中标注资料来源；不直接复制受不同许可证约束的实现文件。
- 为零债务、零价格、禁用抵押、eMode、stable debt、陈旧数据和 indexing error 建立明确行为。
- 健康因子对比 Aave 官方界面，验收误差为 `max(0.01, 0.5%)`；超出即视为 P0 缺陷。
- 如果 eMode 无法在 Day 3 前正确支持，则遇到 eMode 钱包必须返回 `unsupported`，不能给出错误风险等级或派生指标。
- Stress Ladder 使用固定的 collateral-only USD price shock `-5%/-10%/-20%`，债务价值不变；计算必须复用同一个 health factor 核心，禁止单独写一套近似公式。
- Liquidation Buffer 在相同静态假设下计算 `1 - 1 / health_factor`，并复用同一个 health factor 核心；只有证据完整、债务非零且 health factor 为有限值并大于 1 时显示。
- Risk Delta 仅对可比快照做数值差分；没有经验证的事件时，输出不做因果归因。

比赛内可以使用经过人工确认的固定输入作为单元测试 fixture，但正式运行、demo 和评委复现必须查询实时 Graph 数据。

## LLM 决策

不在赛前锁定具体供应商和模型版本，因为最终取决于开赛时可用的 API key。接口与行为现在锁定：

- 输入：确定性当前风险、Liquidation Buffer、Risk Delta、Stress Ladder、Evidence Receipt、精简 evidence、数据时间和缺失字段。
- 输出：结构化标题、三条以内关键发现、建议检查项和 evidence refs。
- 温度低，限制输出长度，不允许工具调用或链上交易执行。
- 模型失败、超时或输出校验失败时，退回确定性模板报告。
- 开赛日选择一个服务端 SDK 实现，不同时维护多个模型供应商。
- 链上 token 名称、ENS 文本和交易 memo 均视为不可信数据，不能进入 system instruction。

## CI 与测试分层

每个提交至少通过：

1. `ruff check`。
2. `ruff format --check`。
3. 单元测试：数学、规则、地址、report id、序列化和输出长度。
4. 契约测试：Graph JSON → Pydantic 模型，覆盖字段缺失、Graph errors 和 `_meta`。
5. SQLite 集成测试：快照顺序、报告读取与过期、幂等和迁移。
6. Web 集成测试：首页、分析 API、报告页、三个引导问题、429、错误页与 secret 不泄漏。

带密钥的实时 Graph smoke test 不应在外部 pull request 自动运行。它通过手动 workflow 或本地命令执行，并保存 block/time 作为验收证据。静态 fixture 只用于测试，不作为 demo 数据。

## 逐日实施顺序

### 9月4日，Day 0：基线与资格

- Fork、保留许可证、创建 `upstream-baseline` tag。
- 提交完整 `PRE_EXISTING.md`。
- 创建受限 Studio API key，完成 Aave `_meta` 和真实仓位查询。
- 记录实际 Subgraph ID、schema、block、查询延迟和测试地址。
- 建立最小 `pyproject.toml`、Python 3.12 环境和 lockfile。

退出条件：公开 Git 历史能证明基线；一个真实地址从官方 Aave Subgraph 返回非空仓位。未达到时停止 Web 工作。

### 9月5日，Day 1：Graph Gateway

- 共享 AsyncClient、Bearer 鉴权、显式 timeout、有限重试和错误类型。
- `_meta` 新鲜度与 indexing error 检查。
- Aave queries、分页和原始响应契约模型。
- Graph 故障、429、超时、partial data 契约测试。

退出条件：命令行或测试服务能稳定生成带 source metadata 的原始 Aave Snapshot。

### 9月6日，Day 2：Aave 归一化

- Reserve 与 UserReserve 合并。
- scaled supply、variable/stable debt、价格与抵押开关归一化。
- 缺失数据和 eMode 标记。
- 建立至少三个真实钱包的比较记录：无仓位、普通仓位、接近风险仓位。

退出条件：Normalized Snapshot 不依赖 FastAPI 或 LLM，并能序列化保存。

### 9月7日，Day 3：风险数学

- WAD/RAY、利息、资产价值、加权清算阈值和 health factor。
- 规则 v1：liquidatable、danger、warning、healthy、incomplete。
- 与 Aave 官方界面对比并形成 golden tests。
- 用同一 health factor 核心实现 -5%、-10%、-20% Stress Ladder，覆盖零债务、缺价格和 unsupported 场景。
- 在同一限定情景下实现 Liquidation Buffer，覆盖 health factor 小于等于 1、无限值、零债务和不完整证据。

退出条件：三个测试地址均通过误差门槛，Stress Ladder 与 Liquidation Buffer 复用已验证的数学核心；无法支持的状态明确拒绝给出等级或派生指标。

### 9月8日，Day 4：快照存储与 Risk Delta

- 固定 SQLite schema、schema version 和快照序列化。
- 可比快照选择、总量和按资产差分、`no_baseline`/`incomparable` 行为。
- 保存 source metadata、规则版本、情景假设和 evidence refs。
- 测试 block 顺序、deployment/schema 不一致和重复快照。

退出条件：Risk Delta 能对两份可比真实快照给出可复核差分；不可比输入明确拒绝比较。

### 9月9日，Day 5：无账号 Web 端到端路径

- import-safe FastAPI 生命周期、HTML 首页与健康检查。
- 地址表单、`POST /api/analyze`、`GET /reports/{report_id}` 与来源展开。
- Graph → Snapshot → Risk → 持久化 report → 服务端 HTML/JSON。
- 报告显示 health factor、确定性等级、Liquidation Buffer、Risk Delta、Stress Ladder 和 Evidence Receipt。
- 首次查询显示 `no_baseline`；Graph 断开时显示失败而不是旧结果冒充实时结果。
- 浏览器响应、HTML 与日志均不包含 Graph key 或模型 key。

退出条件：不依赖 LLM 的真实端到端 demo 已可录屏。

### 9月10日，Day 6：AI 解释与引导追问

- 冻结实际 LLM 供应商和模型。
- 严格输入/输出 schema、evidence refs、长度限制和确定性 fallback。
- AI 摘要只解释当前风险、Risk Delta、Liquidation Buffer 与 Stress Ladder。
- `POST /api/reports/{report_id}/explain` 只接受三个固定意图：“发生了什么”“什么先失守”“如何核验”。
- 覆盖模型超时、拒绝、无效 JSON、无证据结论与 prompt injection。

退出条件：AI 不改变任何数值或等级，至少一个引导问题引用正确 evidence refs；关闭模型仍可使用确定性报告。

### 9月11日，Day 7：部署、可靠性与 Uniswap Gate

- 单容器、单 worker、持久化 volume、健康日志和优雅关停。
- 在非开发机环境公开运行无需账号的核心 Web 路径。
- 为匿名请求增加全局并发上限、地址冷却时间、请求体限制和清晰的 429 响应；不保存原始 IP。
- 完整错误矩阵、速率限制、重试退避和取消处理。
- secret scan、日志脱敏、依赖审计。
- 手工验证 Graph 是 load-bearing：禁用它后核心分析不能正常完成。
- 只有公开核心通过上述检查且无 P0/P1 后，才开始 Uniswap De-risking Preview：目标 health factor 反推、实时路线、价格影响、来源时间与不可用状态。
- Uniswap 模块最多占用 4 小时；不连接钱包、不签名、不执行交易。

退出条件：公开部署可使用，Graph 失效时明确停止；没有已知 P0/P1 缺陷，CI 全绿。Uniswap 未完成不阻止核心退出，但不能选择该 Partner Prize。

### 9月12日，Day 8：Bazantic Gate、复现与提交初稿

- README 从零启动步骤、环境变量、数据流和 Graph 说明。
- 评委复现脚本与公开测试地址。
- 从干净环境完成安装和全量测试。
- 完成提交表单草稿、截图和 2–4 分钟 demo 初稿。
- 录制一次“Graph 不可用即停止”的短片段，不展示密钥。
- 若核心稳定，最多用 3 小时创建 Bazantic x402/MPP Gateway、Recipe 和严格 A/B 测试；普通 Web 不依赖 Bazantic。
- 若 Uniswap 已通过真实报价验收，让 Recipe 串联 Wallet Vitals 与 Uniswap；否则只申报可真实证明的 Bazantic Continuity 能力。
- 完成 Uniswap `FEEDBACK.md` 与反馈表，以及 Bazantic 所需的输入、输出、改进说明和录屏。

退出条件：非开发机环境至少连续运行 2 小时；仓库、README、视频初稿和提交文案均可复核。每个拟选 Sponsor 都有独立的资格证据包。

### 9月13日，Day 9：冻结与提交

- 不再增加功能。
- 从干净 checkout 完整复现。
- 核对 baseline tag、最终 tag、PRE_EXISTING、许可证和 Git 历史。
- 录制或重录最终视频，验证公开链接。
- 默认选择 The Graph、Uniswap Foundation 和 Bazantic；逐项核对资格证据，未通过的 Sponsor 当场删除。
- 内部目标为 10:00 EDT 前提交，保留两小时处理平台或视频故障。

退出条件：最迟 12:00 EDT 前，仓库、视频、提交页面和 prize/pool 选择全部可公开访问。

## Milestone Gates

| Gate | 截止 | 必须满足 | 未满足时 |
|---|---|---|---|
| G0 | 9月4日 + 6小时 | 官方 Aave Subgraph 返回真实仓位 | 不做 Web，先解决数据源 |
| G1 | 9月7日晚 | health factor 通过真实对照；Stress Ladder 复用同一核心 | 删除复杂信号，只保留可验证事实与固定压力情景 |
| G2 | 9月9日晚 | 公开 Web 报告实时展示当前风险、Liquidation Buffer、Risk Delta、Stress Ladder 和 Evidence Receipt | 砍全部 stretch，专注核心演示 |
| G3 | 9月11日 12:00 EDT | AI 有证据引用和可靠 fallback；公开部署可用；CI 无 P0/P1 | 砍全部 Sponsor 扩展，保留 The Graph 核心报告路径 |
| G3U | 9月11日 20:00 EDT | Uniswap 真实报价、去杠杆数学、失败状态和测试通过 | 不选 Uniswap；不得用硬编码路线补资格 |
| G4 | 9月12日 12:00 EDT | Bazantic gateway、Recipe、A/B 证据完成；部署、测试、README 可复现 | 不选 Bazantic，优先完成视频与提交 |
| G5 | 9月13日 10:00 EDT | 仓库、视频和提交表单均已完成 | 立即提交当前稳定版本，保留两小时故障缓冲 |

## 缺陷优先级

- **P0**：错误风险数值、数据源不是实时 Graph、服务端密钥进入浏览器、核心路径崩溃。
- **P1**：陈旧数据未标记、匿名请求可轻易耗尽额度、无法从干净环境启动、AI 虚构证据。
- **P2**：页面排版、非关键交互、可选数据源失败。

存在任何 P0 时禁止开发新功能；存在 P1 时禁止开始 Uniswap 或 Bazantic。Uniswap 没有通过 G3U 时，Bazantic 只能包装已稳定的风险 API，不能假装串联一个不存在的报价步骤。

## 明确砍项顺序

遇到时间不足时依次删除：

1. Bazantic gateway、Recipe 和第三 Sponsor 申报。
2. Uniswap De-risking Preview 和第二 Sponsor 申报。
3. Token API、Pinax Substreams、ENS 与非 Aave 风险信号。
4. 报告永久链接，改为有保留期的 `report_id`。
5. 自由文本追问，只保留三个固定引导意图。
6. Risk Delta 的按资产细分，保留总抵押、总债务和 health factor 差分。
7. 页面动画与复杂图表，保留单页分区、清晰表格和错误状态。

不能删除的最小差异化核心：实时 Aave Subgraph、确定性当前风险、Liquidation Buffer、至少一个可比快照的 Risk Delta、固定假设的 Stress Ladder、Evidence Receipt、一次基于证据的 AI 解释、公开代码和可复现 demo。模板 fallback 是可靠性措施，不能代替最终 demo 中的 AI 路径。

## 官方依据

- [FastAPI Templates 文档](https://fastapi.tiangolo.com/advanced/templates/)
- [FastAPI Static Files 文档](https://fastapi.tiangolo.com/tutorial/static-files/)
- [FastAPI Docker 部署文档](https://fastapi.tiangolo.com/deployment/docker/)
- [HTTPX AsyncClient 文档](https://www.python-httpx.org/api/)
- [uv 项目与 lockfile 文档](https://docs.astral.sh/uv/guides/projects/)
- [Ruff linter 与 formatter 文档](https://docs.astral.sh/ruff/)
- [Aave 官方 Subgraph 仓库](https://github.com/aave/protocol-subgraphs)
- [Aave V3 MathUtils 协议参考](https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/math/MathUtils.sol)
- [已归档的 Aave Utilities 说明](https://github.com/aave/aave-utilities)
- [ETHOnline 2026 Prize Magnet 组合](13-prize-magnet-selection.md)
