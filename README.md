# HashBurst Node

Canonical source repository for the HashBurst Node runtime.

## Status

Development / release-candidate preparation. Not mainnet-ready.

The stable protocol baseline is **HashBurst Node API and Protocol Contract v1.0.0**. It was frozen from the behavior exercised by HashBurst Node dev3 and dev4 Stage A. Mining exploration from dev4 Stage B remains experimental until it is wired into the signed control dispatcher, protected by persistent anti-replay before side effects, and validated by a live provider canary.

## Responsibilities

- persistent node identity and enrollment integration
- Ed25519 signed control plane
- persistent anti-replay
- Core runtime and capability reporting
- MiningControlProvider abstraction
- Mining Accelerator / AI1 integration
- experimental signed mining exploration
- future TEP runtime integration
- future P2P / Federation integration
- future Sovereignty client integration

## Security invariants for v0.1.0-rc1

- private node keys remain local
- signed, target-bound and expiring intents only
- persistent anti-replay
- signed results bound to the exact intent digest
- `production_apply=false`
- no arbitrary shell execution
- no controller-supplied executable paths or arbitrary URLs
- no silent miner, policy or history modification

## Repository boundaries

The AI1 implementation belongs in `hashburst/mining-accelerator`.
TEP protocol/runtime development belongs in `hashburst/tep`.
Installation and deployment orchestration belongs in `hashburst/node-installer`.
The historical public blockchain remains in `hashburst/blockchain`.

## Compatibility target

The historical dev3/dev4 Stage A bridge was validated against Mining Accelerator 0.1.2. The first Node RC targets Accelerator 0.1.3 and must prove compatibility through contract tests before release.

See `docs/protocol/API-CONTRACT-v1.md`.
