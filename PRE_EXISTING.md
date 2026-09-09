# Wallet Vitals Pre-existing Work Disclosure — Draft

> Replace every bracketed value after the event starts. Keep this file in the public submission repository and link it from the main README.

## Upstream project

- Submission project: **Wallet Vitals**
- Submission repository: `wallet-vitals`
- Project: `dorukyy/telegram-wallet-tracker`
- Upstream repository: <https://github.com/dorukyy/telegram-wallet-tracker>
- License: MIT
- Audited upstream commit: `c96f64078ffcf1cc3090778591ad4971ac48292f`
- Fork created: `2026-09-09 after participant acceptance and explicit authorization to begin event-period work`
- Submission repository baseline commit/tag: `[commit and tag]`

## What existed before ETHOnline 2026

The upstream project provided a Python Telegram bot with commands to add, remove, and list tracked wallet addresses. It stored wallet registrations in SQLite, periodically queried Ethereum, BNB Chain, and WAX data providers, and sent basic incoming/outgoing native-transfer notifications.

The pre-existing implementation did **not** include The Graph, ENS resolution, normalized token or DeFi positions, wallet risk scoring, approval analysis, liquidation-risk analysis, an AI copilot, evidence-grounded explanations, a web dashboard, or a production API.

At the audited baseline, the application did not run successfully on our modern Python environment without modification. Its Etherscan/BscScan V1 integration was deprecated, and its Telegram dependency stack was incompatible with the installed modern `urllib3` version.

## Work created during ETHOnline 2026

The following sections must be completed from the final Git history, demo, and test results:

- Live The Graph integration and the exact Aave deployment used.
- Aave position normalization and immutable evidence snapshots.
- Deterministic risk math, Liquidation Buffer, Risk Delta, and Stress Ladder.
- Evidence-grounded AI explanation interface.
- Accountless web interface, JSON API, report persistence, tests, CI, and deployment work.
- If completed and verified: Uniswap de-risking preview and exact product/API used.
- If completed and verified: Bazantic gateway, Recipe, and reproducible A/B evidence.
- Dependency and architecture modernization required for the event product.

## Attribution and code provenance

Files retained or adapted from upstream remain covered by the MIT license and preserve upstream attribution. New work is identifiable through commits made after the baseline tag. The repository history, this disclosure, the main README, and the demo video show the boundary between pre-existing and event-period work.

## Reproducibility

- Baseline tag: `[baseline tag]`
- Final demo tag: `[final tag]`
- Setup instructions: `[README section link]`
- Live Graph data sources: `[README section link]`
- Test command and result: `[command/result]`
- Demo video: `[2–4 minute video URL]`

## AI assistance disclosure

AI tools were used as development aids for `[research / coding / tests / documentation — edit as accurate]`. Product decisions, architecture, integration, validation, and the substantive event-period implementation were performed and reviewed by the team. Any AI-generated code included in the repository was tested and remains attributable through Git history.
