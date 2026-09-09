# Wallet Vitals

[![CI](https://github.com/fizix100/wallet-vitals/actions/workflows/ci.yml/badge.svg)](https://github.com/fizix100/wallet-vitals/actions/workflows/ci.yml)

> Know your liquidation risk before the market does.

Wallet Vitals is an accountless, evidence-grounded Aave V3 risk copilot built for ETHOnline 2026. Paste a public Ethereum address to get deterministic health metrics, a uniform-price Stress Ladder, comparable Risk Delta, and an Evidence Receipt that identifies the exact indexed source behind the report.

No sign-up, Telegram account, wallet connection, signature, or private key is required.

## What it does

- Rebuilds current Aave V3 supply and debt from scaled balances, liquidity/borrow indices, rates, and source-block time.
- Computes health factor from liquidation-weighted collateral and total debt using deterministic Decimal/RAY math.
- Shows a Liquidation Buffer and fixed `-5%`, `-10%`, and `-20%` collateral-only Stress Ladder.
- Stores comparable snapshots and reports collateral, debt, and health-factor changes without claiming unsupported causality.
- Reads Aave's own oracle at the indexed block hash and cross-checks the reconstructed account against `getUserAccountData` at that same block.
- Attaches the Graph deployment, source block/time, query time, rules version, scenario assumptions, position references, oracle/pool addresses, and contract cross-check to every report.
- Uses OpenAI only to explain locked, structured facts. If the model is unconfigured or unavailable, the complete report still works with deterministic explanations.
- Fails closed on stale/indexing-error blocks, malformed data, RPC failures, block mismatches, unsupported eMode, and materially inconsistent indexed accounts.

## Why The Graph is load-bearing

The live product queries the [`protocol-v3` Aave V3 Ethereum Subgraph](https://thegraph.com/explorer/subgraphs/Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g?view=Query) through The Graph Network gateway. Position balances, reserve indices and rates, liquidation thresholds, collateral flags, and indexed source metadata originate in that query. Removing `GRAPH_API_KEY` makes new analyses return `503`; there is no mock or alternative position-discovery path in the running app.

Live testing found that the Subgraph's block was current while some indexed prices had stopped updating in 2024. Production therefore does **not** use its price fields for valuation. A read-only Ethereum RPC supplies `getAssetPrice(address)` from Aave's oracle, with the pool and oracle resolved from the official [Ethereum addresses provider](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Ethereum.sol) at the same block. Every contract call uses EIP-1898 `{blockHash, requireCanonical: true}`. Chain ID, block number, timestamp, and any Graph-provided hash must agree; there is no fallback to `latest` or external market quotes. The Graph remains necessary for positions and historical comparisons.

The reconstructed account is checked against Aave's [`getUserAccountData`](https://github.com/aave/aave-v3-origin/blob/main/src/contracts/interfaces/IPool.sol). Totals must agree within 1 part per million or $0.000001 (whichever is greater); health factor allows 0.0002 absolute or 1 basis point relative for protocol/threshold rounding. Zero/nonzero balances and severity must agree. These are numerical consistency checks, not guarantees of investment safety or independent RPC consensus. Oracle values describe what Aave used at that block; underlying feed freshness is not independently certified.

The browser never receives the Graph or OpenAI key. The gateway call is server-side and authenticates with a Bearer header rather than putting the key in a URL.

```text
Public address
      ↓
The Graph → indexed positions + evidence block
                           ↓
Same-block Aave oracle + account cross-check (read-only RPC)
      ↓
Deterministic risk engine → snapshot history
      ↓
Risk report + Evidence Receipt
      ↓
Optional grounded OpenAI wording (fallback always available)
```

## Run locally

Requirements: Python 3.12, [`uv`](https://docs.astral.sh/uv/), and a The Graph API key with access limited to the Aave Subgraph where possible.

```bash
git clone https://github.com/fizix100/wallet-vitals.git
cd wallet-vitals
cp .env.example .env
# Set GRAPH_API_KEY in .env. OPENAI_API_KEY is optional.
uv sync --locked --extra dev
uv run wallet-vitals
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The JSON API is documented at `/docs`, and `/health` reports whether live Graph analysis is configured.

### Environment variables

| Variable | Required | Default / purpose |
|---|---:|---|
| `GRAPH_API_KEY` | Yes | Server-only The Graph gateway credential |
| `GRAPH_SUBGRAPH_ID` | Yes | `Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g` (Aave V3 Ethereum) |
| `GRAPH_MAX_AGE_SECONDS` | No | `900`; analysis fails if the indexed block is older |
| `ETHEREUM_RPC_URL` | No | `https://ethereum-rpc.publicnode.com`; mainnet RPC supporting hash-pinned `eth_call`, no extra key required by default |
| `OPENAI_API_KEY` | For AI demo | Optional at runtime; required to demonstrate the AI prize path |
| `OPENAI_MODEL` | No | `gpt-5.6-luna` |
| `DATABASE_PATH` | No | `data/wallet_vitals.db` |
| `REPORT_TTL_HOURS` | No | `24` |
| `ADDRESS_COOLDOWN_SECONDS` | No | `10` |
| `MAX_CONCURRENT_ANALYSES` | No | `4` |

### API

```bash
curl -sS http://127.0.0.1:8000/api/analyze \
  -H 'content-type: application/json' \
  -d '{"address":"0x0000000000000000000000000000000000000000"}'
```

- `POST /api/analyze` creates a 24-hour report from a fresh indexed snapshot.
- `GET /reports/{report_id}` opens a shareable, credential-free report page.
- `GET /api/reports/{report_id}` returns its structured evidence.
- `POST /api/reports/{report_id}/explain` accepts only `what_changed`, `what_breaks_first`, or `how_to_verify`.

## Test and verify

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
```

Unit and integration tests cover Aave RAY interest math, liquidation-weighted health factor, stress monotonicity, snapshot comparability, Graph freshness/indexing failure, hash-pinned oracle reads, wrong networks, missing prices, RPC failure, account mismatches (including false empty wallets), retired reports, SQLite idempotency, and Web behavior with the data provider disabled. Test fixtures never appear in the production data path.

For a live smoke test, start the app and analyze a public address with a non-empty, non-eMode Ethereum Aave V3 position. The public address `0xc950fe241c50f93d872edb5a97066474c84c2394` was validated on 2026-09-09; its future position can change. Expand the receipt and inspect the reconstructed and contract health factors at the same block. Confirm the narrative label is `AI · evidence locked` if demonstrating the AI path. Never commit `.env` or paste either key into a browser URL. See [LIVE_VALIDATION.md](LIVE_VALIDATION.md) for actual checks and limitations.

## Risk model and limitations

For enabled collateral asset `i`, Wallet Vitals computes:

```text
health factor = Σ(collateral USDᵢ × liquidation thresholdᵢ) / total debt USD
liquidation buffer = 1 − 1 / health factor
```

The buffer and Stress Ladder hold debt USD value and protocol parameters constant while moving every enabled collateral price by the same percentage. They are static sensitivity tests, not forecasts, guarantees, liquidation-time estimates, or financial advice. They are deliberately collateral-only shocks even when an asset also appears on the debt side. eMode is currently rejected: legacy indexed category matching is insufficient for modern category bitmap rules. Incomplete, negative-balance, or inconsistent indexed positions are rejected rather than silently omitted. A historical report does not establish the wallet's current liquidation state.

Reports using the retired `aave-v1` indexed-price rules cannot be served or explained; the user must run a fresh check under `aave-v2-pinned-oracle`.

Severity labels are a UI aid around the protocol-native health factor: `liquidatable ≤ 1.00`, `danger ≤ 1.10`, `warning ≤ 1.25`, then `healthy`. A zero-debt position is explicitly `no_debt`.

## Deployment

The included container uses one process so the SQLite snapshot history and in-memory cooldown are consistent. Mount `/data` as a persistent volume and set server-side secrets in the hosting platform.

```bash
docker build -t wallet-vitals .
docker run --rm -p 8000:8000 \
  -e GRAPH_API_KEY \
  -e OPENAI_API_KEY \
  -v wallet-vitals-data:/data \
  wallet-vitals
```

## ETHOnline 2026 provenance

This repository extends [`dorukyy/telegram-wallet-tracker`](https://github.com/dorukyy/telegram-wallet-tracker) at commit `c96f64078ffcf1cc3090778591ad4971ac48292f`. The unchanged upstream state is tagged `upstream-baseline`. [PRE_EXISTING.md](PRE_EXISTING.md) records what existed before the event; [UPSTREAM_README.md](UPSTREAM_README.md) preserves the original README.

Wallet Vitals implementation began after acceptance on 2026-09-09 (Asia/Shanghai). The old polling bot is retained only as disclosed upstream source and is excluded from the new package, runtime, container, and checks. The event-period application lives under `src/wallet_vitals/`; its architecture, Web UI, Graph adapter, Aave math, storage, AI boundary, tests, and deployment files are new.

The current qualifying target is **The Graph — Best AI Tooling or AI Use Case with The Graph (Continuity)**. Uniswap and Bazantic remain gated extensions and must not be claimed unless real integrations and their separate qualification evidence are completed.

## Repository map

```text
src/wallet_vitals/
  graph/         The Graph positions, same-block oracle, and account cross-check
  domain/        strict evidence/report models and deterministic risk math
  storage/       SQLite snapshot and expiring report store
  ai/            optional OpenAI Responses adapter with deterministic fallback
  application/   orchestration, concurrency limit, and address cooldown
  web/           FastAPI routes
  templates/     accountless report page
  static/        responsive CSS and small browser client
tests/           deterministic and integration checks
research/        pre-event research and acceptance gates
```

## License and attribution

The upstream MIT license and copyright notice remain in [LICENSE](LICENSE). Event-period additions use the same repository license.
