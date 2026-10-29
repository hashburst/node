# Source provenance

## HashBurst Node dev4 Stage A

Verified artifacts:

- original ZIP: `HashBurst-Node-0.1.0-dev4.zip`
- SHA-256: `ff0402e314b1f6736c2422c740eba54cba9439dc7d574ecfe628233e69e0bef6`
- later received parent ZIP: `HashBurst-Node-0.1.0-dev4(1).zip`
- SHA-256: `214b7ea34ee88b38934c374eee52d4f8480cd77854bb5d0f75a0aac1872cbce8`

Both archives were extracted and compared recursively on 2026-10-29. Their extracted trees are identical. The ZIP digest difference is therefore packaging metadata, not source-content divergence. Both internal SHA256SUMS manifests verify completely.

Stage A contains the dev1-dev4 regression tests and the Core signed control/mining planning implementation.

## HashBurst Node dev4 Stage B

- ZIP: `HashBurst-Node-0.1.0-dev4-stageB.zip`
- SHA-256: `0f710ceaa6cc1c895e8c611a698ebf1fcacd146a35f8c15f45bb139c47c35ba6`
- internal SHA256SUMS: fully verified
- declared parent: `HashBurst-Node-0.1.0-dev4(1).zip`
- declared parent SHA-256: `214b7ea34ee88b38934c374eee52d4f8480cd77854bb5d0f75a0aac1872cbce8`

Stage B adds exploration.py, exploration_journal.py, a RainbowMiner binding example, Stage-B documentation and tests. It remains experimental and is not promoted into Stable Core v1 by source import.

## Import policy

Stable Stage A source is imported as the historical Core implementation baseline. Stage B additions are kept explicitly experimental until dispatcher integration, persistent pre-side-effect anti-replay and provider canary requirements pass.
