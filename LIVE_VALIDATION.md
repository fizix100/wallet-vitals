# Live validation — 2026-09-09

This records actual tests, not a promise about future balances, oracle values, sponsor eligibility, or public deployment.

## Resolved issue

The configured Graph key works. Live queries returned current indexed blocks without indexing errors, but the Subgraph's USDT and USDC indexed oracle timestamps were still in 2024. Production valuation now uses the Aave oracle at the same evidence block hash, not those indexed price fields. The Graph still supplies the positions, indices, rates, thresholds, collateral state, and evidence metadata. No additional API key was needed for the default public Ethereum RPC.

All contract calls are read-only. Pool and oracle addresses are resolved through the Aave Ethereum addresses provider. Chain ID and block metadata are checked, and every `eth_call` is hash-pinned with `requireCanonical: true`. There is no `latest` or market-price fallback. Indexed totals and reconstructed health factor must reconcile within the documented rounding bounds in [README.md](README.md).

## Successful live case

Public test address: `0xc950fe241c50f93d872edb5a97066474c84c2394`. This address is a public integration-test input; no claim is made about its owner.

- Evidence block: `25939073`, timestamp `2026-09-09T09:59:11Z`.
- Block hash: `0x525be902d30a3ddfe95460353bea687704c9da63dbcc1ffa4e2c55bd271bc063`.
- Graph deployment: `QmX2VfvEspbShTdcjefWeG3CKBVXKWm9naxH6TVhqPb9qY`.
- Non-empty WETH/USDT position. Displayed collateral `$6,708.71`, debt `$4,881.61`.
- Reconstructed health factor: `1.1407`; same-block Aave contract: `1.140654571026435845`; cross-check `matched`.
- Stress health factors: `1.0836`, `1.0266`, `0.9125` for the fixed collateral-only declines.
- OpenAI summary returned successfully and passed the numeric/identifier guards. The browser displayed `AI · evidence locked`.
- Second check was comparable with block `25939061`. The rounded deltas were zero; the UI did not invent a change.
- “How do I verify?” returned an explanation tied to this evidence block.
- The report page and JSON API loaded after a server restart.
- Copy-link button visibly changed to `Copied` without the former asynchronous event-reference failure. The resulting report route was separately verified; browser automation did not expose the clipboard text.

An empty-position control (`0xd8da6bf26964af9d7eed9e03e53415d37aa96045`) matched the same-block zero-debt Aave account at block `25939049`.

## Fail-closed cases

- The public address `0x8327e20a05516c9be8dd305e517cd742b629e00f` was rejected because its indexed account did not match the same-block contract within the configured bounds. At diagnostic block `25939069`, indexed debt was `0.24219504516` USD versus contract debt `0.24217205` USD. This diagnostic did not create a report or weaken production checks.
- `0x552b42287c4fe1e913ea9a159b69bd7e9b81ec76` returned a negative indexed scaled balance and was rejected rather than silently dropping the asset.
- Previously saved reports using `aave-v1` now return `404` with an explicit instruction to run a fresh check. They remain in local storage for provenance, but cannot be served or explained as valid reports.
- Automated tests cover stale/missing indexed prices replaced only by valid same-block oracle evidence; wrong chain, mismatched number/hash/timestamp, malformed hash, invalid oracle currency/unit, zero price, RPC rejection/failure, eMode, false-empty accounts, wrong thresholds, and severity-boundary disagreements.

## Local checks and screenshots

`uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run pytest`, and `git diff --check` passed. **46 tests passed** on Python 3.12. The wheel and source distribution also built successfully with `uv build`.

A final live check at block `25939108` again passed the account cross-check; the summary used the deterministic fallback, while an explanation reached OpenAI. That explanation confused entry into `danger` with the first liquidation boundary even though its numbers were grounded. “What breaks first?” is therefore now answered deterministically from the first `liquidatable` scenario, with a regression test that forbids an AI call for that intent. Other optional AI wording remains subject to numeric/identifier checks, not a claim of perfect semantic validation. Each explanation now labels its actual generation mode.

Browser checks used the actual running local app with live provider responses. Desktop width `1280` and mobile width `390` had no document-level horizontal overflow. The metric grid occupied the full report container at both widths. Three unaltered product screenshots are in [submission-assets](submission-assets/README.md); these are not generated/mock metrics. The separate cover is disclosed AI-generated artwork.

## Remaining boundaries

- eMode and inconsistent indexed accounts are intentionally unsupported, not silently approximated.
- Aave oracle reads establish contract values at the evidence block, not independent underlying feed freshness or a current liquidation guarantee.
- Public RPC availability is not guaranteed. Provider failure stops analysis; it does not serve stale data.
- The public demo URL, demo video, and actual registered ETHGlobal track remain separate submission gates. These checks do not establish prize qualification or constitute submission.
- API keys stay server-side in ignored local configuration. None are included in screenshots, the repository, or this document.
