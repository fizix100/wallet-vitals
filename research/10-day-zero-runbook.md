# Wallet Vitals Day 0 操作 Runbook

编制时间：2026-09-01，Asia/Shanghai。本文是开赛日操作清单，不包含已执行的参赛操作或功能实现。

## 一条不可违反的规则

在 ETHGlobal Hacker Dashboard 或官方 kickoff 通知能确认活动已开始之前，不执行本文的 fork、tag、提交、Graph 产品接入或参赛代码命令。

活动列表只给出 9 月 4 日的日期，不足以推定精确 kickoff 时刻。不用本地零点自行开始。

## 执行前的人工确认

- [ ] Hacker Dashboard 显示已可开始 hacking，或已收到官方 kickoff 通知。
- [ ] 记录官方开始时间、页面 URL、本地时区和 UTC 换算。
- [ ] 保存一张能显示开始状态与时间的截图，不包含个人资料或 token。
- [ ] 重新打开活动详情、奖项总览、The Graph、Uniswap Foundation、Bazantic 和提交页，确认截止时间与资格文字没有再变。
- [ ] 在提交表单中选择 Continuity 奖池，确认没有误选名称相近的 From Scratch 奖池。
- [ ] GitHub、The Graph Studio、Uniswap Developer Platform、Bazantic、选定的 LLM 服务和部署平台均能登录；Bazantic 可用 GitHub 或邮箱，不依赖 Telegram。
- [ ] 任何 API key 都只准备放入环境变量或部署 secrets，不粘贴到文档、issue、截图或 shell 历史。

任一项未通过时，先解决账户或时间证据，不开始实现。

## 当前本机就绪快照

复查时间：`2026-09-01T22:13:33+08:00`。本轮只完成通用工具安装与 daemon 启动，未初始化比赛项目。

| 项目 | 状态 | 备注 |
|---|---|---|
| Git | 就绪 | `2.50.1` |
| Python 3.12 | 就绪 | `3.12.13` |
| 系统 `python3` | 风险 | 当前是 `3.14.6`；项目命令禁止依赖裸 `python3` |
| `uv` | 就绪 | `0.12.8`，通过 Homebrew 安装 |
| GitHub CLI | 就绪 | `2.92.0`，当前认证可用 |
| Git identity | 就绪 | name/email 已配置，本文不记录具体值 |
| Docker | 就绪 | CLI/server `29.2.1`，daemon 已运行，`linux/aarch64` |
| FFmpeg | 就绪 | `8.1.2`，可用于视频检查与转码 |
| 磁盘空间 | 就绪 | 当前工作盘约 431 GB 可用 |
| 赛前工作区 | 就绪 | 空 Git repo、无 commit、无 remote；只有 `README.md` 和 `research/` |
| `wallet-vitals/` 提交目录 | 就绪 | 当前不存在，留给 kickoff 后 clone |

### 已完成的通用环境准备

1. 已用 Homebrew 安装 `uv 0.12.8`。这是 Astral 官方列出的 macOS 安装方式。
2. 已启动 Docker Desktop，`docker info` 验证成功。未创建容器、image 或项目文件。

开赛前或重启电脑后可重新运行以下检查，不初始化项目：

```bash
uv --version
python3.12 --version
docker info
gh auth status
```

## Day 0 前 90 分钟

### 0–10 分钟：记录资格证据

1. 完成上方人工确认。
2. 记录开始时刻：

```bash
date -u '+%Y-%m-%dT%H:%M:%SZ'
date '+%Y-%m-%dT%H:%M:%S%z %Z'
```

3. 保存当时的 Continuity、AI 工具披露、版本控制和 The Graph AI Continuity 资格文字。
4. 如果页面与 `08-rules-recheck-and-test-wallets.md` 冲突，先更新规则记录和日程，不继续 fork。

### 10–25 分钟：Fork 与基线 tag

在赛前工作区的父子边界内创建新的提交仓库，不把当前空 repo 原地改造成 fork：

```bash
wallet_vitals_root="/Users/feng/Documents/ChatGPT/OSS"
wallet_vitals_submission_dir="${wallet_vitals_root}/wallet-vitals"
wallet_vitals_upstream_commit="c96f64078ffcf1cc3090778591ad4971ac48292f"

test ! -e "$wallet_vitals_submission_dir"
cd "$wallet_vitals_root"
gh repo fork dorukyy/telegram-wallet-tracker --fork-name wallet-vitals --clone
cd "$wallet_vitals_submission_dir"
```

验证 remote、审计 commit 和 MIT 授权。任一验证失败都停止：

```bash
git remote -v
git fetch upstream --tags
git cat-file -e "${wallet_vitals_upstream_commit}^{commit}"
test -f LICENSE -o -f LICENSE.md
if test -f LICENSE; then
  rg -n "MIT License" LICENSE
else
  rg -n "MIT License" LICENSE.md
fi
```

在审计 commit 上建立不可混淆的 baseline tag 和比赛分支：

```bash
git show-ref --verify --quiet refs/tags/upstream-baseline && exit 1
git switch --detach "$wallet_vitals_upstream_commit"
test "$(git rev-parse HEAD)" = "$wallet_vitals_upstream_commit"
git tag -a upstream-baseline "$wallet_vitals_upstream_commit" -m "Upstream baseline before ETHOnline 2026 work"
git push origin refs/tags/upstream-baseline
git switch -c codex/ethonline-2026 "$wallet_vitals_upstream_commit"
```

如果 GitHub 已有同一上游的 fork，`gh repo fork` 可能复用旧 fork 而不是新建。遇到这种情况时不删除任何仓库；先确认 remote、默认分支和所有权，再决定是复用 fork 还是创建独立公开仓库。

### 25–40 分钟：提交 Continuity 披露

1. 保留上游 LICENSE 和版权信息。
2. 把赛前研究作为明确标记的 pre-event artifacts 加入新仓库，不把它们冒充为比赛期间成果：

```bash
cp -R ../research ./research
cp ../README.md ./PRE_EVENT_RESEARCH.md
cp research/02-PRE_EXISTING.draft.md ./PRE_EXISTING.md
```

3. 立即把 `PRE_EXISTING.md` 中的 fork UTC 时间、baseline tag 和实际仓库信息补齐。所有仍然带方括号的字段都必须是明确的未完成占位，不能装作既成事实。
4. 提交前确认只有文档变化：

```bash
git status --short
git diff --check
git diff --name-only "$wallet_vitals_upstream_commit"
```

5. 独立提交并推送披露：

```bash
git add PRE_EXISTING.md PRE_EVENT_RESEARCH.md research
git commit -m "docs: disclose upstream baseline and pre-event research"
git push -u origin codex/ethonline-2026
```

### 40–60 分钟：The Graph 资格探针

1. 在 The Graph Studio 创建低额度、可撤销的受限 API key。
2. 不把 key 写进 `.env.example`、README、查询文件或截图。
3. 先对官方 Aave V3 Ethereum Subgraph 执行 `_meta` 查询，记录 deployment、block/time、`hasIndexingErrors` 和查询延迟。
4. 再使用 `08-rules-recheck-and-test-wallets.md` 中的公开候选地址执行 `userReserves` 查询。
5. 保留一个空仓位和一个非空仓位返回；所有记录带查询时间，不把动态数字写成永久预期。

P0 验收：真实 Graph provider 同时返回新鲜 `_meta` 和至少一个非空用户仓位。未通过时不初始化 Bot、SQLite、AI 或压力测试模块。

### 60–75 分钟：创建可复现 Python 3.12 骨架

只有 Graph P0 通过后才执行：

```bash
uv init --python 3.12
uv python pin 3.12
uv add 'fastapi[standard]==0.141.1' httpx==0.28.1 pydantic==2.13.5 pydantic-settings==2.15.0 eth-utils==6.0.0 aiosqlite==0.22.1
uv add --dev pytest==9.1.1 pytest-asyncio==1.4.0 ruff
uv lock
uv sync --locked
uv run python --version
```

`uv run python --version` 必须显示 Python 3.12。不用系统裸 `python3`，因为当前它指向 3.14.6。

本时段只建立锁定依赖和最小 import/test 骨架，不赶着同时实现 Web、Graph、数学和 AI。

### 75–90 分钟：建立首个实现提交和停止点

1. 建立并通过最小 import test。
2. 生成并提交 `pyproject.toml`、`.python-version`、`uv.lock` 和最小测试。
3. 运行：

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
git diff --check
git status --short
```

4. 提交信息建议：`build: establish reproducible Python 3.12 project`。
5. 推送后停止 5 分钟，核对 G0 证据和下一个提交边界。不在未确认 Graph schema 时开始写大量 adapter。

## 前 90 分钟的完成定义

- [ ] 官方开始时刻有可复核记录。
- [ ] GitHub fork 公开可访问，`origin`/`upstream` 无混淆。
- [ ] `upstream-baseline` 精确指向 `c96f64078ffcf1cc3090778591ad4971ac48292f`。
- [ ] MIT License 与上游 attribution 保留。
- [ ] `PRE_EXISTING.md` 和赛前研究已以独立文档提交。
- [ ] 真实 Aave Subgraph `_meta` 新鲜且无 indexing error。
- [ ] 至少一个公开候选地址返回非空 `userReserves`。
- [ ] Python 3.12 和 `uv.lock` 可从干净环境复现。
- [ ] 已推送一个只包含披露的 docs commit 和一个最小 build commit。
- [ ] 没有 secret 或未披露的赛前产物进入 Git 历史。

## 立即停止条件

- 无法证明官方 kickoff 已开始。
- fork 所有权、remote 或 baseline commit 不明确。
- LICENSE 与审计时不一致。
- Graph `_meta` 有 indexing error、数据显著陈旧或所有候选地址均无法查询。
- 任何 secret 出现在 `git diff`、终端截图或已推送 commit。
- `uv run python --version` 不是 Python 3.12。
- 为了赶进度准备用 RPC、Etherscan 或 fixture 冒充正式 Graph 主链路。

## 开赛后的提交粒度

建议前六个 commit 保持如下边界：

1. `docs: disclose upstream baseline and pre-event research`
2. `build: establish reproducible Python 3.12 project`
3. `feat(graph): add authenticated gateway and metadata validation`
4. `feat(aave): normalize live reserve and user evidence`
5. `feat(risk): calculate verified Aave account risk and stress ladder`
6. `feat(web): expose an accountless evidence report`

Risk Delta、SQLite snapshot 和 AI narrator 继续分开提交。不把整个产品压成一个“initial implementation”。

## 参考

- [ETHOnline 2026 提交详情](https://ethglobal.com/events/ethonline2026/info/details)
- [The Graph ETHOnline 2026 奖项](https://ethglobal.com/events/ethonline2026/prizes/the-graph)
- [GitHub CLI `repo fork`](https://cli.github.com/manual/gh_repo_fork)
- [Astral uv 安装文档](https://docs.astral.sh/uv/getting-started/installation/)
- [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
