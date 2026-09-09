# Wallet Vitals

Wallet Vitals is an accountless, evidence-grounded Aave risk copilot for ETHOnline 2026. Paste a public Ethereum address to inspect its live Aave V3 position, deterministic health metrics, comparable snapshot changes, stress scenarios, and the evidence behind every result.

> See what changed. Stress-test what could happen. Verify every result.

## Event status

This repository extends [`dorukyy/telegram-wallet-tracker`](https://github.com/dorukyy/telegram-wallet-tracker) at commit `c96f64078ffcf1cc3090778591ad4971ac48292f`. The unchanged upstream state is tagged `upstream-baseline`; [PRE_EXISTING.md](PRE_EXISTING.md) records what existed before the event. [UPSTREAM_README.md](UPSTREAM_README.md) preserves the original project description.

Implementation of Wallet Vitals began after the participant reported that the ETHOnline 2026 application had been accepted and explicitly authorized event-period development on 2026-09-09 (Asia/Shanghai). The repository history separates preparation material from implementation commits.

## Target experience

- No sign-up, Telegram account, wallet connection, or signature.
- Live Aave V3 Ethereum evidence queried through The Graph.
- Protocol-native health factor and deterministic severity; no invented 0–100 score.
- Liquidation Buffer, fixed-assumption Stress Ladder, and comparable Risk Delta.
- Evidence Receipt containing deployment, block/time, query time, rules version, assumptions, and evidence references.
- AI explanations that cite calculated evidence and cannot change the numbers.
- Optional, gated Uniswap de-risking preview and Bazantic agent workflow only after the core passes its reliability gates.

## Planned Partner Prizes

1. The Graph — Best AI Tooling or AI Use Case with The Graph (Continuity).
2. Uniswap Foundation — Best Uniswap Stack Contribution, only if the live unsigned preview is complete.
3. Bazantic — Help an Agent Use Your Hackathon Project, only if the gateway, Recipe, and A/B evidence are complete.

A partner will be removed from the final submission if its qualification evidence is incomplete.

## Documentation

- [PRE_EXISTING.md](PRE_EXISTING.md) — pre-existing versus event-period work.
- [PRE_EVENT_RESEARCH.md](PRE_EVENT_RESEARCH.md) — preparation index captured before implementation.
- [research/03-the-graph-migration-spec.md](research/03-the-graph-migration-spec.md) — architecture and product boundary.
- [research/04-kickoff-and-acceptance-checklist.md](research/04-kickoff-and-acceptance-checklist.md) — acceptance gates.
- [research/06-implementation-backlog.md](research/06-implementation-backlog.md) — implementation sequence.
- [research/13-prize-magnet-selection.md](research/13-prize-magnet-selection.md) — Partner Prize selection rationale.

## Development

The application code, environment variables, test commands, live Graph deployment, and deployment instructions will be documented here as they are implemented and verified. Planned behavior is not presented as completed behavior.

## License and attribution

The upstream MIT license and copyright notice remain in [LICENSE](LICENSE). Event-period additions are distributed under the same repository license unless noted otherwise.
