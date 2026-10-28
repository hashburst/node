# HashBurst Node API and Protocol Contract v1.0.0

Status: **FROZEN CORE CONTRACT**

Protocol family: HashBurst Node  
Signature algorithm: Ed25519  
Digest: SHA-256  
Mainnet status: NOT YET MAINNET  
Production apply in RC profile: DISABLED

## 1. Compatibility rule

A schema identifier ending in `-v1` has immutable semantics once released. Any incompatible change to required fields, field meaning, canonicalization, signature input, authorization, replay behavior or security boundary requires a new protocol/schema version.

Implementation and protocol versions are independent.

## 2. Signed envelope

Stable wire envelope: `hb-node-control-envelope-v1`.

```json
{
  "algorithm": "Ed25519",
  "format": "hb-node-control-envelope-v1",
  "key_id": "<signing-key-id>",
  "kind": "<intent|result>",
  "payload": {},
  "signature": "<ed25519-signature>"
}
```

The signature must be verified before envelope metadata is trusted.

## 3. Control intent

Stable payload schema: `hb-control-intent-v1`.

```json
{
  "schema": "hb-control-intent-v1",
  "intent_id": "<unique-id>",
  "controller_id": "<controller-id>",
  "node_id": "<target-node-id>",
  "issued_at": 0,
  "expires_at": 0,
  "scope": "<authorization-scope>",
  "action": "<action>",
  "parameters": {},
  "production_apply": false
}
```

Before execution the Node verifies envelope, signature, controller, target, schema, scope, action, time bounds, replay state and action-specific constraints. Invalid intents fail closed and cause no side effect.

## 4. Anti-replay

`intent_id` is single-use within its authorization context. Anti-replay state is persistent. Replay returns a signed result with `result=NACK` and `reason=replay_detected`.

For privileged actions replay checking occurs before the first external side effect.

## 5. Control result

Stable payload schema: `hb-control-result-v1`.

Core fields are `schema`, `intent_id`, `intent_sha256`, `controller_id`, `node_id`, `processed_at`, `result`, `reason`, `scope`, `action`, `production_apply`, `network_calls`, `miner_configuration_modified`, `history_or_policy_modified`, and `observation`.

Results are signed by the Node. `intent_sha256` binds the result to the exact processed intent.

## 6. Stable RC scope

`control-read-only` permits observation, analysis and proposal generation only. It does not authorize permanent miner changes, wallet changes, credential changes, arbitrary command execution, arbitrary filesystem writes, arbitrary network calls or production APPLY.

## 7. Stable actions

- `probe.status`
- `probe.capabilities`
- `mining.status`
- `mining.telemetry.snapshot`
- `mining.accelerator.shadow`
- `mining.predict.decide`

Observed schemas include:

- `hb-node-mining-capabilities-v1`
- `hashburst-accelerator-status-v1`
- `hb-node-mining-telemetry-snapshot-v1`
- `hb-node-mining-shadow-result-v1`
- `hashburst-accelerator-shadow-v1`
- `hb-node-mining-plan-result-v1`
- `hb-mining-proposal-v1`

`mining.predict.decide` creates a signed, expiring proposal. Mandatory decision gates are freshness, thermal, health and economics. Proposal generation is not proposal execution.

## 8. AI1 boundary

The stable sequence is OBSERVE -> PREDICT -> DECIDE -> SIGNED PROPOSAL.

A signed proposal does not itself modify miner configuration. Execution requires a separately authorized operation.

## 9. MiningControlProvider

Provider-specific control is behind a local abstraction conceptually exposing `capture_state`, `read_state`, `apply_transient` and `restore`.

Controller intents carry semantic intent, not executable paths, shell commands, arbitrary scripts or arbitrary URLs. RainbowMiner is a provider backend, not part of the public HashBurst Core protocol.

## 10. Experimental Mining Exploration Profile

Reserved as experimental-v1:

- `hb-mining-exploration-proposal-v1`
- `hb-mining-exploration-intent-v1`
- `hb-mining-exploration-receipt-v1`
- `hb-rainbowminer-binding-v1`

State machine:

`received -> validated -> authorized -> prestate_captured -> executing -> verified -> committed`

Failure/rollback states:

`rollback_started -> rolled_back` or `failed`.

Exploration is not permanent APPLY. Successful exploration restores baseline after measurement. Thermal or health failure triggers rollback. Promotion to stable requires dispatcher wiring, persistent anti-replay before side effects and a live provider canary.

## 11. Permanent APPLY

Permanent production APPLY is excluded from RC1. A future APPLY protocol requires a distinct privileged scope/action, signed target-bound and expiring intent, proposal binding, anti-replay before side effect, pre-state capture, verification, rollback and signed receipt.

`production_apply=true` is never inferred.

## 12. TEP/Federation/Sovereignty boundary

TEP, P2P, Federation, Sovereignty and AI2 use independent versioned protocol specifications. They may reuse the Node cryptographic identity foundation but do not silently extend `hb-control-intent-v1`.

The TEP protocol is not frozen by this document.

## 13. Conformance

Core conformance requires automated tests for valid intent, invalid signature, wrong controller, wrong node, expiry, replay, unsupported scope/action, forbidden side effects, signed result, exact intent-digest binding and disabled production apply.

Exploration conformance additionally requires local binding, proposal/action binding, pre-side-effect anti-replay, pre-state capture, thermal/health watchdogs, deterministic rollback, baseline restoration and signed receipt.
