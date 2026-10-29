# Verification report — controlled source import

Date: 2026-10-29
Gate: **OPEN — NOT YET VERIFIED COMPLETE**

## Artifact verification

- HashBurst-Node dev4 Stage A parent ZIP SHA-256: `214b7ea34ee88b38934c374eee52d4f8480cd77854bb5d0f75a0aac1872cbce8`
- HashBurst-Node dev4 Stage B ZIP SHA-256: `0f710ceaa6cc1c895e8c611a698ebf1fcacd146a35f8c15f45bb139c47c35ba6`
- Mining Accelerator 0.1.3 ZIP SHA-256: `d796b6d3519a073bca93fd2591a7642f3baf86f4c17aa04e13cb1151b27c15c3`
- Accelerator 0.1.3 `accelerator.py` SHA-256: `5bcff576a5ebb0b63d6d21eacfe07fba0d19a6040d2ebacc234fa59ff933549b`

All internal SHA256SUMS manifests passed after extraction.

## Exact-artifact test execution

With `PYTHONDONTWRITEBYTECODE=1`:

- Stage A: 7/7 PASS
  - dev1: 4
  - dev2: 1
  - dev3: 1
  - dev4: 1
- Stage B: 11/11 PASS
  - Stage A regression: 7
  - Stage B: 4
- Mining Accelerator 0.1.3: 11/11 PASS

## Stage A to Stage B comparison

The Stage A Core implementation and dev1-dev4 tests are byte-identical in Stage B. Stage B changes its README/manifest and adds:
- STAGEB-BUILD.json
- config/rainbowminer-binding.example.json
- docs/STAGE-B.md
- hashburst_node/exploration.py
- hashburst_node/exploration_journal.py
- tests/test_stageb.py

## Gate condition

These PASS results validate the verified source artifacts, but they do **not** by themselves satisfy the canonical-repository gate. VERIFIED COMPLETE requires:

1. all static source/config/docs/tests transferred byte-identically;
2. generated `__pycache__`, `*.pyc` and runtime state excluded;
3. repository file SHA-256 values compared with the artifact baseline;
4. dev1-dev4, Stage B and Accelerator tests rerun from the canonical repository contents;
5. all comparisons and tests PASS.

Until all five conditions pass, v0.1.0-rc1 assembly must not begin.
