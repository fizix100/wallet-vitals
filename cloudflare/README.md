# Cloudflare deployment

Live app: https://onebattle.win/wallet-vitals/

Video: https://onebattle.win/wallet-vitals/demo

This native Python Worker shares the local application's risk, Graph, oracle and narration
modules. D1 replaces SQLite; a Fetch-backed httpx transport replaces sockets. Secrets stay in
Worker bindings. The existing `onebattle.win/*` Worker and its database are not modified:
only `/wallet-vitals` and `/wallet-vitals/*` are routed to this application.

## Reproduce

From the repository root:

```sh
uv sync --locked --extra dev
uv run pytest
uv run python scripts/prepare_cloudflare.py
cd cloudflare
uv sync --locked
uv run pywrangler sync
npx wrangler d1 execute wallet-vitals-reports --remote --file schema.sql
uv run pywrangler deploy
```

The account must already be authenticated in Wrangler. For a different Cloudflare account,
create a separate D1 database and update the account, database and route configuration first.
Set `GRAPH_API_KEY` and optional `OPENAI_API_KEY` using `wrangler secret put`, or `secret bulk`
with JSON on standard input. Never place credentials in command arguments, committed files,
browser URLs or client-side JavaScript. Deployment preserves existing secret bindings.

`scripts/prepare_cloudflare.py` copies only application source, frontend assets and, when present,
the generated demo video/subtitles. It never copies `.env` or local databases. Generated bundle,
dependency and video files are ignored by Git. To reproduce the video, follow `demo-video/README.md`.

## Runtime pin and RPC

Compatibility date is deliberately pinned to **2026-09-07** (Python 3.13). On September 9,
the new Python 3.14 snapshot runtime deployed successfully but failed before request handling
with error 1101. The same application worked with Python 3.13. A compatibility-date change
requires `uv run pywrangler sync --force --upgrade`, followed by live verification; otherwise
the cached wasm dependencies can target the wrong Python version. Both uv and wasm lockfiles
are checked in. Do not advance the date blindly.

The public Worker uses dRPC's documented public Ethereum endpoint, `https://eth.drpc.org`,
because PublicNode returned HTTP 429 to the Cloudflare deployment. It uses the same hash-pinned
Aave contract reads and validation; there is no fallback to latest blocks, fixture data or
unverified market prices. Public RPC availability is not guaranteed.

## Public-demo safeguards

- Atomic D1 quotas: 6 paid/analysis requests per IP per minute, one analysis per address per
  10-second bucket, and 100 total paid/analysis requests per UTC day, across both public hosts.
- Completed explanations are cached by report and intent. A first analysis can include AI
  narration; repeat report reads do not call Graph, RPC or OpenAI.
- Report URLs are unlisted, **not private**, and expire after 24 hours. Snapshots are retained
  for up to 7 days for comparisons. Cleanup runs during subsequent analysis requests.
- Quota IP identifiers are daily hashes; raw IPs are not stored in the application database.
- No cross-origin POSTs, no wallet signatures, no write transactions. Bodies are limited to 2 KB.
- Observability was enabled temporarily during diagnosis and is disabled for the public demo.
  Diagnostic messages contain error types/hostnames/statuses, not keys or upstream response bodies.
- Demo MP4/VTT are served through the asset binding. The verified response was a complete
  HTTP 200 body (about 4.5 MiB); byte-range support is not assumed.

These limits bound intended API consumption; they are not a promise of zero hosting charges
or a substitute for account-level budget monitoring. No paid plan was purchased for this deployment.

## Local Worker check

```sh
cd cloudflare
npx wrangler d1 execute wallet-vitals-reports --local --file schema.sql
uv run pywrangler dev --port 8787
```

Visit `http://localhost:8787/wallet-vitals/`. Without secret bindings the page explicitly
shows that live data is not configured. Local FastAPI/SQLite usage remains unchanged.
