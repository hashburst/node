# v0.1.0-rc2 conformance record

Status: CANDIDATE - final CI required after this record/SBOM commit
Date: 2026-10-29

Preliminary verified implementation commit: `61cd1ce350cc031f5231e269dfb18482db4195ee`
GitHub Actions run: `40864847605`
Conclusion: SUCCESS

## Passed gates

- RC1 and RC2 static release gates: PASS
- Enrollment 0.2.0-dev3 exact ZIP SHA-256, internal SHA256SUMS, declared `cryptography==50.0.2`, and 67 tests: PASS
- Node dev1-dev4 regression: PASS
- Historical Stage B regression in isolated tree: PASS; experimental Stage B remains non-shipping evidence
- Mining Accelerator 0.1.3 exact source provenance and tests: PASS
- RC2 adversarial controlled-exploration runtime tests: PASS
- Tampered proposal/intent, replay, changed binding and signed `production_apply=true` rejection: PASS
- Thermal, health, telemetry-staleness and deadline watchdog rollback: PASS
- Runtime/telemetry exception rollback: PASS
- Successful exploration exact baseline restoration: PASS
- Rollback failure explicitly reports `rollback_failed` and never claims restoration: PASS
- Local watchdog caps cannot be relaxed remotely: PASS
- Permanent APPLY schema/API absent from RC2 exploration runtime: PASS
- RC2 manifest and RC1 manifest/SBOM JSON syntax: PASS
- RC2 install/upgrade preserves identity, anti-replay and completed exploration evidence: PASS
- RC2 executable rollback preserves persistent state: PASS
- Interrupted exploration blocks executable rollback and preserves recovery evidence: PASS
- `production_apply=false`: PASS
- `mainnet=false`: PASS

## Release policy

Run `40864847605` is preliminary evidence only. This record and the RC2 SBOM change the repository tree. The eventual tag `v0.1.0-rc2` may point only to the new candidate commit containing this record and SBOM after that exact commit's complete `rc2-conformance` workflow concludes SUCCESS.

No production APPLY or mainnet capability is enabled by this candidate.
