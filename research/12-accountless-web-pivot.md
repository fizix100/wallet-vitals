# Wallet Vitals 无账号 Web 方案

决策时间：2026-09-01，Asia/Shanghai。由于不再采用 Telegram，本文冻结新的产品外壳。本文是赛前规格，不包含参赛实现。

## 最终决策

Wallet Vitals 将作为公开、只读、无需账号的 Web 应用参赛。用户只需粘贴公开 EVM 地址，不注册、不连接钱包、不签名，也不提供邮箱、手机号、私钥或助记词。

The Graph、LLM、Uniswap 和部署凭据只保存在服务端。浏览器收到经过验证的报告，不直接访问带密钥的 Graph gateway、报价服务或模型服务。Bazantic 仅作为可选 agent/API 通道；普通 Web 用户无需 Bazantic 账号或支付。

## 为什么选择 Web

- 评委打开链接即可体验，低于 Bot、Discord 或 CLI 的使用门槛。
- 可以同时展示 Risk Delta、Liquidation Buffer、Stress Ladder 和 Evidence Receipt，信息层级比聊天消息更清楚。
- 服务端保护 Graph 与模型密钥，避免把受限凭据放进前端。
- 单个 FastAPI 服务即可提供页面、JSON API、OpenAPI、健康检查和部署入口，无需 React/Node 构建链。
- 公开 Web 更直接证明 Practicality、Usability 和可复现性。

## 用户路径

1. 打开公开 HTTPS 首页。
2. 粘贴 Ethereum 地址，点击 **Analyze live position**。
3. 页面显示查询进度，并从服务端生成实时 Graph 报告。
4. 报告依次显示当前风险、Liquidation Buffer、Risk Delta、Stress Ladder、AI Brief 和 Evidence Receipt。
5. 用户可点击“发生了什么”“什么先失守”“如何核验”三个固定问题。
6. 用户可通过有保留期的匿名报告 URL 重新打开结果；页面明确显示报告生成时间，不冒充持续实时状态。

## 最小接口

```text
GET  /                         HTML 首页
POST /api/analyze              提交地址并生成报告
GET  /reports/{report_id}      打开匿名报告
GET  /api/reports/{report_id}  获取结构化报告
POST /api/reports/{report_id}/explain
GET  /api/reports/{report_id}/de-risk-preview  条件启用的 Uniswap 预览
GET  /healthz                  进程健康，不代表 Graph 数据健康
```

`report_id` 必须不可预测且不包含地址、密钥或个人信息。API 不提供任意 GraphQL 代理，避免被用来消耗团队额度。

## 页面边界

首版只有一个输入页和一个报告页。报告页采用固定顺序：

1. 当前等级、health factor、Liquidation Buffer。
2. Risk Delta。
3. Stress Ladder。
4. AI Brief 与三个固定引导问题。
5. Evidence Receipt、数据新鲜度和假设。

不用钱包连接按钮、登录导航、用户头像、价格走势图、复杂 dashboard、交易按钮或自动补仓入口。

## 匿名请求保护

- 限制地址和请求体长度，只接受支持网络的合法地址。
- 对 Graph 查询设置全局并发上限和按地址冷却时间。
- 重复请求优先复用同一 source block 下的有效结果，但页面必须清楚标记生成时间与是否重新查询。
- 429、Graph timeout、indexing error 和 stale data 使用不同错误状态。
- 不保存原始 IP；只记录必要的聚合运行指标。
- 报告按明确保留期过期，SQLite 不无限增长。
- HTML、JSON、日志和错误追踪均执行 secret 泄漏测试。

## Continuity 边界

上游仓库仍是 `dorukyy/telegram-wallet-tracker`，但 Telegram 只属于如实披露的 pre-existing work，不进入目标依赖。

继承的是公开钱包登记、SQLite 状态和轮询比较概念。比赛期间新增无账号 Web、FastAPI 生命周期、Graph gateway、Aave 归一化、风险数学、快照比较、AI、匿名可靠性、测试和部署。最终以 baseline tag、Git diff 和 `PRE_EXISTING.md` 为准。

## 失败降级

- Web 样式延期：保留服务端 HTML，不退回账号型平台。
- JavaScript 失败：基本地址表单和报告仍能通过服务端提交完成。
- LLM 失败：显示确定性报告和明确的 AI unavailable 状态。
- Graph 失败或陈旧：停止核心分析，不用 RPC、Etherscan、旧缓存或 fixture 冒充成功。
- 部署平台失败：切换容器平台，但保持同一公开 HTTP 接口和 SQLite 持久化要求。

## 开赛前边界

赛前只冻结本规格和研究材料。FastAPI 文件、HTML、CSS、路由、容器和部署均在官方 kickoff 后创建，并通过 `PRE_EXISTING.md` 和 Git 历史明确归入 event-period work。

## 参考

- [FastAPI Templates](https://fastapi.tiangolo.com/advanced/templates/)
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/docker/)
- [ETHOnline 2026 提交与评审](https://ethglobal.com/events/ethonline2026/info/details)
- [The Graph ETHOnline 2026 奖项](https://ethglobal.com/events/ethonline2026/prizes/the-graph)
