# ETHOnline 2026 Submission Draft

## Project name

Wallet Vitals

## One-line description

An accountless Aave V3 risk copilot that turns live The Graph evidence into deterministic liquidation diagnostics, stress tests, snapshot changes, and explanations with receipts.

## Project description

Wallet Vitals helps a DeFi user answer four questions before an Aave position becomes urgent: What is my current health factor? How much uniform collateral downside reaches the liquidation boundary? What changed since my last check? Which tested stress scenario fails first?

The user pastes a public Ethereum address without signing in, connecting a wallet, or signing a message. The server queries the live Aave V3 Ethereum Subgraph through The Graph Network, rebuilds accrued supply and debt balances from protocol indices and rates, and reads Aave oracle prices at the same block hash through read-only Ethereum RPC. It cross-checks totals and health factor against the Aave pool before producing the Liquidation Buffer and fixed `-5%/-10%/-20%` Stress Ladder. Repeated checks produce a Risk Delta only when the source deployment, rules, address, network, and block order are comparable. Unsupported eMode and inconsistent evidence stop analysis explicitly.

Every report includes an Evidence Receipt with the Graph subgraph and deployment, indexed block and timestamp, query time, rules version, scenario assumptions, and position references, plus the oracle/pool addresses, pinned block hash, and contract account cross-check. An optional OpenAI Responses adapter converts only the precomputed facts into a short explanation. The model cannot alter the structured report values; numeric and identifier guards reject unsupported narrative claims, and deterministic explanations remain available if the model is absent or fails.

## How it was built

- Python 3.12 and FastAPI for an import-safe async Web/API service.
- The Graph Network gateway and the `protocol-v3` Aave V3 Ethereum Subgraph.
- Aave oracle and pool `eth_call` reads pinned to the same Ethereum block hash, with no transactions.
- Strict Pydantic evidence/report contracts and Decimal/RAY protocol math.
- SQLite for idempotent evidence snapshots and 24-hour shareable reports.
- Server-rendered HTML, responsive CSS, and small dependency-free JavaScript.
- Optional OpenAI Responses API narrative layer with a deterministic fallback.
- `uv`, Ruff, Pytest, GitHub Actions, and a one-process Docker deployment.

## The Graph integration

The Graph is load-bearing. The live Aave query supplies balances, reserve indices/rates, liquidation parameters, collateral state, and source block metadata. There is no mock or alternate position-discovery route; disabling the server-side Graph key stops new analyses. During live testing we found frozen indexed prices despite a current block. The fix reads Aave's oracle at that exact block hash and checks the indexed account against the pool; it does not fabricate prices or replace The Graph with unrelated market data. The application rejects stale blocks, indexing errors, unsupported eMode, and inconsistent accounts.

Subgraph: <https://thegraph.com/explorer/subgraphs/Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g?view=Query>

## Track and Partner Prize

- Intended ETHGlobal track: Continuity / Extend Open Source. The participant form previously showed “start from scratch”; actual registration track has not been verified. Do not claim Continuity eligibility is confirmed.
- Intended Partner Prize: The Graph — Best AI Tooling or AI Use Case with The Graph (Continuity), subject to the registered track and final official eligibility.

The baseline is the tagged upstream commit `upstream-baseline`. Full pre-existing versus event-period disclosure is in `PRE_EXISTING.md`.

## Links to fill after the live gate

- Public repository: <https://github.com/fizix100/wallet-vitals>
- Live demo: `[pending]`
- Demo video (2–4 minutes): `[pending]`
- Final demo tag: `[pending]`

## Suggested 3-minute demo flow

1. Open the home page and emphasize that there is no login, wallet connection, or signature.
2. Analyze a public address with a non-empty Aave V3 Ethereum position.
3. Show health factor, liquidation buffer, the three stress scenarios, and the first `no_baseline` state.
4. Re-run after a later indexed block and show the comparable Risk Delta.
5. Expand the Evidence Receipt and point to The Graph deployment, block/time, same-block Aave oracle/pool proof, contract health factor, assumptions, and evidence references.
6. Ask “What breaks first?” and “How do I verify?” to show grounded explanation.
7. Briefly disable the Graph key or show the prepared failure capture to prove The Graph is load-bearing.
8. End on the public repository, `upstream-baseline` tag, and green CI run.
