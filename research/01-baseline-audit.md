# 候选基线审计：dorukyy/telegram-wallet-tracker

## 结论

`dorukyy/telegram-wallet-tracker` 适合作为“跟踪公开钱包并比较变化”的 Continuity 基线，不适合作为运行时产品外壳或链上数据实现直接延续。它的钱包登记和轮询概念已经成形，但 Etherscan/BscScan V1 数据源失效，Telegram 依赖栈也无法在现代 Python 环境中直接启动。这形成清晰的改造边界：保留上游 attribution 和钱包快照概念，比赛期间重写为无需账号的 Web 交互、实时 Graph 数据与风险分析主链路。

## 审计快照

| 项目 | 结果 |
|---|---|
| 上游仓库 | <https://github.com/dorukyy/telegram-wallet-tracker> |
| 审计提交 | `c96f64078ffcf1cc3090778591ad4971ac48292f` |
| 最后提交日期 | 2023-09-23 |
| 许可证 | MIT |
| 审计时热度 | 18 stars / 12 forks |
| 代码规模 | 6 个 Python 文件，约 23 KB |
| 本地环境 | Python 3.12 |

热度数据只代表审计时快照，提交前应重新确认。

## 原项目已有能力

- Telegram 多用户命令交互：`/start`、`/add`、`/remove`、`/list`。
- 按 Telegram chat 保存跟踪地址。
- SQLite 钱包登记和轮询游标。
- ETH、BSC、WAX 三条链的轮询任务。
- ETH/BSC 原生币转入、转出方向判断与通知文本。
- WAX 活动查询和通知。

## 原项目没有的能力

- The Graph 或其他 Subgraph/Substreams 数据接入。
- ENS 解析。
- ERC-20 资产明细、授权暴露和 DeFi 仓位归一化。
- Aave 健康因子、清算风险、集中度等风险指标。
- AI 推理或自然语言钱包报告。
- Web 仪表盘、认证、计费、API、Webhook。
- 自动化测试、CI、Docker 和结构化日志。

## 运行实测

| 检查项 | 结果 | 说明 |
|---|---|---|
| 依赖安装 | 部分通过 | 基础包可安装；旧版 Bot SDK 与现代依赖不兼容。 |
| 模块导入 | 部分通过 | 数据与 SQLite 模块可单独导入。 |
| SQLite CRUD | 通过 | 钱包登记基础操作可工作。 |
| CoinGecko 价格请求 | 通过 | 审计时实时请求成功。 |
| Etherscan 交易请求 | 失败 | V1 API 返回弃用错误。 |
| `main.py` 启动 | 失败 | `python-telegram-bot 13.15` 间接引用已被现代 `urllib3` 移除的 `urllib3.contrib.appengine`。 |

## 关键技术风险

1. `main.py` 在 import 时直接实例化并启动机器人，难以测试和复用。
2. Etherscan/BscScan V1 已失效；API 返回错误字符串后，调用方仍可能按交易列表遍历并崩溃。
3. 启动时会重置链上时间戳，可能丢掉停机期间的交易；而且禁用的网络仍可能触发 API 调用。
4. 同步 HTTP 请求运行在机器人回调和轮询路径中，没有统一超时、重试、退避或速率限制。
5. SQLite 表名由 network 拼接；保存路径有部分白名单，读取和删除路径缺少同等约束。
6. 地址、网络和配置输入缺少完整验证；密钥放在明文 `config.ini`。
7. 游标更新语义可能造成重复通知或漏报；通知 POST 的响应没有可靠处理。
8. `telegram~=0.0.1` 与 `python-telegram-bot~=13.15` 的组合陈旧且含义混乱。
9. 没有测试覆盖，任何数据层替换都需要先建立契约测试。

## 可保留与应替换的边界

### 可作为设计参考保留

- 输入公开地址并保存钱包记录的产品动作。
- 使用 SQLite 保存状态的基础概念。
- 周期性获取数据并比较前后变化的产品模型。
- 已存在的 MIT 许可证与上游 attribution。

### 比赛期间应重写

- Telegram、chat 身份模型、Bot SDK 和命令协议。
- 所有链上数据读取与轮询逻辑。
- 数据模型、游标和幂等处理。
- 风险计算、证据模型和 AI 输出。
- 配置、密钥、日志、测试和部署方式。

这意味着最终项目不是对旧脚本进行兼容性修补，也不会继续依赖 Telegram，而是在明确继承钱包跟踪与快照比较概念的前提下，完成以 The Graph 为核心的无账号 Web 产品、新数据层和智能层。
