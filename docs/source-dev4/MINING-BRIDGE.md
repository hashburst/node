# HashBurst Node dev3 mining bridge

Baseline: HashBurst-Mining-Accelerator 0.1.2, external and immutable.

Safety contract:
- no `collect` invocation;
- no RainbowMiner write/restart/switch operation;
- SQLite telemetry snapshot uses `mode=ro&immutable=1` and exports aggregates only;
- `status` invokes the baseline's documented read-only command;
- `shadow` invokes documented `recommend` and writes its new proposal only under Node runtime state;
- accelerator.py, policy.json and history.sqlite are hashed before/after every bridge action;
- production apply is always false.