# HashBurst v0.1.0-rc2 controlled exploration contract

RC2 promotes controlled one-worker exploration from the Stage B evidence into the release-candidate runtime. It does not enable permanent mining configuration APPLY and does not enable mainnet.

## Schemas

- `hb-mining-exploration-proposal-v1`: Node-signed proposal.
- `hb-mining-exploration-intent-v1`: Controller-signed authorization bound to the exact proposal and candidate action.
- `hb-mining-exploration-receipt-v1`: Node-signed terminal evidence.
- `hb-rainbowminer-binding-v1`: local-only binding and allowlist.

## Hard invariants

1. `production_apply` is exactly `false` in proposal, intent and receipt.
2. Exploration is temporary measurement, never permanent APPLY.
3. One worker only. First canary keeps hardware and algorithm unchanged.
4. The controller cannot supply shell, executable paths, target paths, URLs or arbitrary configuration.
5. Local binding pins the target and allowed profiles. Command adapters pin executable SHA-256 and execute with `shell=False`.
6. Intent is accepted once only through the persistent Core anti-replay journal before the first miner mutation.
7. Exact pre-state is captured before mutation.
8. Watchdog continuously evaluates thermal health, telemetry freshness and deadline. Any trip initiates rollback.
9. Normal completion also initiates rollback.
10. A successful terminal receipt requires verified baseline restoration. If restoration cannot be verified, the outcome is `rollback_failed` and `baseline_restored=false`.
11. The receipt binds proposal digest, intent digest, pre-state digest and event-log digest and is signed by the Node.
12. Mainnet remains disabled.

## State machine

`received -> validated -> authorized -> prestate_captured -> executing -> verified -> rollback_started -> rolled_back -> committed`

Any failure after pre-state capture enters `rollback_started`. A verified restoration may terminate as `aborted_restored`; an unverifiable restoration terminates as `rollback_failed`.

## Watchdog

The signed proposal may request stricter limits but cannot relax local policy. Effective limits are the stricter of the proposal and local binding policy for maximum temperature, duration and telemetry staleness. Missing/non-numeric temperature, unhealthy status, stale telemetry or deadline violation fail closed.

## Release boundary

RC2 may transiently change one locally bound worker only for the authorized exploration interval. It must restore baseline before returning a successful receipt. Permanent `hb-mining-apply-intent-v1` remains out of scope.
