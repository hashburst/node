# HashBurst Node resource and capability contract v1

`hashburst/node` is the composition and coordination layer for a HashBurst full node.

It discovers host capabilities and coordinates released components without owning their protocol logic.

## Capability classes

A node may expose any compatible combination of:

- HVM full-node / validator capability from `hashburst/blockchain`;
- TEP capability from `hashburst/tep`;
- mining capability from `hashburst/mining-accelerator`;
- specialist AI capability from `hashburst/AI`;
- mining segmentation capability from `hashburst/mining_segmentation`;
- storage and other independently versioned HashBurst components.

Target hosts include VPS, Raspberry/ARM, Windows desktop, macOS/MacBook, GPU rig and HPC server.

## Protected workload contract

The coordinator treats consensus/validator, TEP and storage workloads as protected capacity. Mining is elastic. A mining optimizer may propose CPU/GPU/thread/intensity/pool/algorithm budgets, but the node coordinator decides whether an actuator is permitted by local health and policy.

No node-side AI may modify HVM consensus validity, APoW target/reward rules, HBT economics or validator governance.

## Environmental data

Node telemetry may transport measured power or lower-quality proxies with explicit provenance. CPU time/load alone is not Joules, CO2e, a carbon credit or a verified environmental asset.

## Installation

`hashburst/node-installer` composes versioned releases for each host role. This repository coordinates them at runtime.
