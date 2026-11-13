# v0.1.0-rc1 conformance record

Status: CANDIDATE - final CI required after this record commit
Date: 2026-10-29

Verified implementation commit: `fa8905ed75438952a7f0704230b1f9256fa997ef`
GitHub Actions run: `40860767800`
Conclusion: SUCCESS

## Passed gates

- Static RC1 invariants: PASS
- Enrollment 0.2.0-dev3 exact artifact SHA-256 `9c6ba3434f5a14dee2bb7bdd8e1b6e87f44418a47e03a0437feda147521ccd73`: PASS
- Enrollment internal SHA256SUMS: PASS
- Enrollment declared dependency `cryptography==50.0.2`: PASS
- Enrollment tests: 67/67 PASS
- Node dev1-dev4 regression: PASS
- Stage B regression: PASS; Stage B remains non-shipping
- Mining Accelerator 0.1.3 exact source hash and tests: PASS
- Release manifest JSON: PASS
- CycloneDX SBOM JSON: PASS
- `production_apply=false`: PASS
- `mainnet=false`: PASS
- Sandbox install: PASS
- Stage B excluded from installed runtime payload: PASS
- Identity state sentinel preserved across install/rollback: PASS
- Anti-replay state sentinel preserved across install/rollback: PASS
- Executable rollback to previous release: PASS

## Release policy

This record does not enable production APPLY or mainnet. The tag `v0.1.0-rc1` may point only to a commit whose own complete `rc1-conformance` workflow concludes SUCCESS. Because this record changes the tree after run 40860767800, one final full CI run is mandatory before tagging.
