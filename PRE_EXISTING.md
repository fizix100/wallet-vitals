# Wallet Vitals Pre-existing Work Disclosure

## Upstream project

- Submission project: **Wallet Vitals**
- Submission repository: `wallet-vitals`
- Project: `dorukyy/telegram-wallet-tracker`
- Upstream repository: <https://github.com/dorukyy/telegram-wallet-tracker>
- License: MIT
- Audited upstream commit: `c96f64078ffcf1cc3090778591ad4971ac48292f`
- Fork created: `2026-09-09 after participant acceptance and explicit authorization to begin event-period work`
- Submission repository baseline: commit `c96f64078ffcf1cc3090778591ad4971ac48292f`, annotated tag `upstream-baseline`

## What existed before ETHOnline 2026

The upstream project provided a Python Telegram bot with commands to add, remove, and list tracked wallet addresses. It stored wallet registrations in SQLite, periodically queried Ethereum, BNB Chain, and WAX data providers, and sent basic incoming/outgoing native-transfer notifications.

The pre-existing implementation did **not** include The Graph, ENS resolution, normalized token or DeFi positions, wallet risk scoring, approval analysis, liquidation-risk analysis, an AI copilot, evidence-grounded explanations, a web dashboard, or a production API.

At the audited baseline, the application did not run successfully on our modern Python environment without modification. Its Etherscan/BscScan V1 integration was deprecated, and its Telegram dependency stack was incompatible with the installed modern `urllib3` version.

## Work created during ETHOnline 2026

Event-period work is isolated under `src/wallet_vitals/` and in the event-period commits. It includes:

- A server-side The Graph Network client and Aave V3 Ethereum Subgraph adapter for Subgraph ID `Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g`. The runtime records the current deployment returned by `_meta` in every receipt.
- Aave position normalization using indexed scaled balances, reserve indices, rates, liquidation thresholds, and collateral flags; same-block Aave oracle prices and an account cross-check via read-only Ethereum RPC. Unsupported eMode positions are rejected.
- Deterministic RAY/Decimal risk math, Liquidation Buffer, Risk Delta, and a fixed-assumption Stress Ladder.
- An optional OpenAI Responses narrative adapter that receives only precomputed structured facts and falls back to deterministic explanations.
- A new accountless FastAPI Web interface and JSON API, shareable expiring reports, SQLite persistence, responsive styling, tests, CI, and a single-process container deployment.
- Provider freshness and indexing-error gates, bounded retry, anonymous per-address cooldown, and analysis concurrency limits.
- A native Cloudflare Python Worker deployment with independent D1 persistence, atomic public-demo quotas, cached explanations, and expiring report links. The existing OneBattle root website is separate from this application.

Uniswap and Bazantic are not implemented or claimed in the current code. They remain possible gated extensions only after the live core has passed qualification checks.

## Attribution and code provenance

Files retained or adapted from upstream remain covered by the MIT license and preserve upstream attribution. New work is identifiable through commits made after the baseline tag. The repository history, this disclosure, the main README, and the demo video show the boundary between pre-existing and event-period work.

## Reproducibility

- Baseline tag: `upstream-baseline`
- Deployed demo source: commit `8eddda7d1e9c85c35059163674c15403d383fdf2`
- Setup instructions: [README — Run locally](README.md#run-locally)
- Live Graph data source: [README — Why The Graph is load-bearing](README.md#why-the-graph-is-load-bearing)
- Test command: `uv run ruff check src tests && uv run ruff format --check src tests && uv run pytest`
- Current verification: see [LIVE_VALIDATION.md](LIVE_VALIDATION.md) for test results and live same-block account checks. Public deployment and the demo video are available below; CI passed all 50 tests at the deployed demo commit.
- Public deployment: <https://onebattle.win/wallet-vitals/>
- Demo video: <https://onebattle.win/wallet-vitals/demo> (3 minutes 9 seconds, 1080p, genuine public-deployment captures with English synthetic narration and subtitles)
- Submission configuration: project and single-participant track were set to Continuity in the ETHGlobal form on 2026-09-09. This is not a claim of judge approval or final eligibility. The form flags the inherited first commit for manual review, and its final declaration still displays from-scratch wording; no inaccurate declaration has been accepted.

## AI assistance disclosure

OpenAI Codex assisted with research, implementation, tests, debugging, deployment, documentation, and submission preparation. Repository history and automated checks document the resulting work; this disclosure does not claim an independent human review. The product uses OpenAI Responses for guarded explanations of precomputed facts. The branded cover illustration was AI-generated; product screenshots are genuine application captures. The edited demo uses macOS Samantha synthetic narration and English subtitles, without music or sped-up playback.
