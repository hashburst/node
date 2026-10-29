# Controlled source import status

Status: VERIFIED COMPLETE
Verified: 2026-10-29

## Canonical commits

- HashBurst Node exact Stage A/B blobs: `974f3454c2208b7666b5d8779bccf7c4c2d710c3`
- Mining Accelerator 0.1.3 exact blobs: `fdfab9d0a74e5e3324cc9f8411fcb64dab0dfcf1`

## Artifact provenance

- Node dev4 Stage A original ZIP SHA-256: `ff0402e314b1f6736c2422c740eba54cba9439dc7d574ecfe628233e69e0bef6`
- Node dev4 Stage A parent ZIP SHA-256: `214b7ea34ee88b38934c374eee52d4f8480cd77854bb5d0f75a0aac1872cbce8`
- Node dev4 Stage B ZIP SHA-256: `0f710ceaa6cc1c895e8c611a698ebf1fcacd146a35f8c15f45bb139c47c35ba6`
- Mining Accelerator 0.1.3 ZIP SHA-256: `d796b6d3519a073bca93fd2591a7642f3baf86f4c17aa04e13cb1151b27c15c3`
- Accelerator 0.1.3 accelerator.py SHA-256: `5bcff576a5ebb0b63d6d21eacfe07fba0d19a6040d2ebacc234fa59ff933549b`

All internal SHA256SUMS manifests passed before import.

## Byte identity

Canonical source blobs were created from Base64 encodings of the original artifact bytes. Git blob SHAs in the canonical repositories were compared against Git blob SHAs calculated directly from the extracted verified artifacts and match exactly.

An earlier text-mediated import normalized line endings on several files. Git-blob verification detected this and the exact-blob commits above supersede it.

## Test gate

Tests were replayed from canonical-layout trees assembled from those exact blobs with `PYTHONDONTWRITEBYTECODE=1`:

- Node Stage A dev1-dev4: 7/7 PASS.
- Node Stage B including dev1-dev4 regression: 11/11 PASS.
- Mining Accelerator 0.1.3: 11/11 PASS.

## Exclusions

Only generated/non-source state is excluded: `__pycache__`, `*.pyc`, runtime databases, keys/passphrases, telemetry/history state and generated observations/proposals.

## Gate decision

VERIFIED COMPLETE. Source provenance/import verification is no longer a blocker for beginning assembly of `v0.1.0-rc1`. This does not enable production APPLY or mainnet.
