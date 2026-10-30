# HashBurst Node

Canonical source repository for the HashBurst Node runtime.

## Status

The current release-candidate line is v0.1.0. The v0.1.0-rc1 baseline covers Core Node, enrollment, read-only Mining Provider integration and AI1 shadow operation. v0.1.0-rc2 adds signed controlled exploration, persistent anti-replay, exact pre-state capture, watchdog enforcement, rollback and Node-signed results.

Mainnet and permanent production application are disabled in this release-candidate line.

## Responsibilities

- persistent node identity and enrollment integration
- Ed25519 signed control plane
- persistent anti-replay
- Core runtime and capability reporting
- MiningControlProvider abstraction
- Mining Accelerator and AI1 integration
- signed controlled mining exploration
- TEP runtime integration boundary
- P2P and Federation integration boundary
- Sovereignty client integration boundary

## Security invariants

- private node keys remain local
- control intents are signed, target-bound and expiring
- anti-replay state is persistent
- signed results are bound to the exact intent digest
- production application remains disabled unless explicitly enabled by a later approved release
- arbitrary shell execution is not accepted
- controller-supplied executable paths and arbitrary URLs are not accepted
- miner configuration, policy and history are not modified outside the defined control path

## Repository boundaries

The AI1 implementation belongs in `hashburst/mining-accelerator`.
TEP protocol and runtime development belongs in `hashburst/tep`.
Installation and deployment orchestration belongs in `hashburst/node-installer`.
The historical public blockchain remains in `hashburst/blockchain`.

## Compatibility

The Node control contract is defined in `docs/protocol/API-CONTRACT-v1.md`. Mining Accelerator compatibility is verified through contract tests before release.
