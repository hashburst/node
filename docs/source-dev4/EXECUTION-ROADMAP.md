# dev4 execution roadmap
Stage A (this package): authenticated `mining.predict.decide` creates an Ed25519-signed, expiring proposal bound to node, Accelerator code hash, policy hash, history hash and telemetry freshness. `production_apply=false` and `apply_supported=false` are invariant.

Gates are fail-closed: freshness, thermal, worker health and economics. A failed gate produces a signed `blocked` proposal rather than an executable recommendation.

Stage B (only after real Stage-A canary PASS): add explicit `mining.apply` with proposal verification, current-state revalidation, narrow executor allowlist, pre-state capture, apply, post-state verify, commit receipt, and automatic rollback on verification failure. No generic shell command execution is permitted.