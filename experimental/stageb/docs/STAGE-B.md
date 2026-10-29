# dev4 Stage B - controlled exploration

Stage B is derived from dev4 Stage A and does not alter the Stage A artifact. It adds a one-worker, fail-closed exploration executor.

Security invariants:
- the controller never supplies a command, executable path, configuration path or arbitrary shell fragment;
- a local `hb-rainbowminer-binding-v1` binds node, normalized worker, hardware and exact allowlisted profile transitions;
- `rainbowminer-command-v1` uses `subprocess` with `shell=False` and requires SHA-256 pinning of the executable;
- `rainbowminer-json-v1` may replace only the single locally bound JSON target and always stores/restores its exact bytes;
- first canary exploration requires the same hardware and algorithm; only an empirically observed, locally allowlisted profile can be selected;
- controller authorization is `hb-mining-exploration-intent-v1`, bound to the signed node proposal SHA-256 and exact candidate action SHA-256;
- pre-state is captured before execution; thermal or health watchdog failure triggers rollback;
- successful exploration also rolls back to baseline before committing its signed receipt. Exploration is measurement, not permanent APPLY;
- no private key, endpoint credential or raw worker identity belongs in controller proposals.

The permanent APPLY path is intentionally not enabled by this package. A successful exploration receipt is evidence for the subsequent `hb-mining-apply-intent-v1`; permanent APPLY must reuse the same binding/pre-state/verify/rollback machinery and be enabled only after a real RainbowMiner local control binding has been validated on the canary.
