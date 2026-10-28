# Implementation status

Updated: 2026-10-28

## Frozen Stable Core v1

The following protocol identifiers are frozen from verified dev3/dev4 Stage A behavior:

- hb-node-control-envelope-v1
- hb-control-intent-v1
- hb-control-result-v1
- hb-node-mining-capabilities-v1
- hb-node-mining-telemetry-snapshot-v1
- hb-node-mining-shadow-result-v1
- hashburst-accelerator-status-v1
- hashburst-accelerator-shadow-v1
- hb-node-mining-plan-result-v1
- hb-mining-proposal-v1

Stable RC actions:

- probe.status
- probe.capabilities
- mining.status
- mining.telemetry.snapshot
- mining.accelerator.shadow
- mining.predict.decide

Stable RC scope: control-read-only.

Known result reasons include accepted_capability_probe, accepted_mining_status, accepted_telemetry_snapshot, accepted_shadow_evaluation, accepted_predict_decide and replay_detected.

## Verified historical implementation evidence

dev3 exercised signed read-only control, persistent anti-replay, capability/status/telemetry/shadow actions and signed ACK/NACK results.

dev4 Stage A added mining.predict.decide and an expiring hb-mining-proposal-v1 with freshness, thermal, health and economics gates. The observed canary remained blocked and production_apply=false.

The historical bridge reported Accelerator 0.1.2. The current RC integration target is Accelerator 0.1.3 and requires fresh contract testing.

## Experimental v1

Reserved, not stable:

- hb-mining-exploration-proposal-v1
- hb-mining-exploration-intent-v1
- hb-mining-exploration-receipt-v1
- hb-rainbowminer-binding-v1

Stage B includes the exploration state machine, semantic profiles, provider binding, pre-state capture, watchdog/rollback and signed receipt concepts. It is not stable until it is integrated into the Node dispatcher and persistent anti-replay is proven before side effects.

## Future / separate protocol work

- permanent production APPLY
- AI2 solo-mining segmentation
- TEP protocol/runtime
- P2P
- Federation
- Sovereignty

These items must not be represented as Stable Core v1 merely because integration hooks exist.
