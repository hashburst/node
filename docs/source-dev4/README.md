# HashBurst Node 0.1.0-dev4

Extends the verified dev3 BI3339M read-only bridge with PREDICT -> DECIDE -> SIGNED PROPOSAL.

New action: `mining.predict.decide`.

The signed proposal binds node identity, expiry, freshness/thermal/health/economic gates, Accelerator 0.1.2 code hash, policy hash, history hash and shadow-decision hash. This Stage-A package deliberately keeps `production_apply=false` and `apply_supported=false`. It does not modify RainbowMiner, policy.json or history.sqlite and makes no network call.

After the real Stage-A canary passes, Stage B will add APPLY -> VERIFY -> COMMIT/ROLLBACK with a narrow executor and automatic rollback; it will not expose arbitrary command execution.