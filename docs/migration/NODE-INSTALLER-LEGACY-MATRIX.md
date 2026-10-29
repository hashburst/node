# node-installer legacy to canonical repository matrix

Status: inventory/mapping only. No file has been removed, moved or disabled in node-installer.

| Legacy area in node-installer | Current responsibility | Canonical destination | Migration disposition |
|---|---|---|---|
| bin/hashburst-node | historical packaged blockchain/node binary | hashburst/node and/or hashburst/blockchain after runtime boundary review | retain legacy binary; do not overwrite |
| install.sh | deployment orchestration | hashburst/node-installer | retain; later consume versioned releases |
| systemd/hashburst-node.service | node service deployment | hashburst/node-installer | retain installer-owned unit |
| tep/ | deployed HB-TEP runtime | hashburst/tep | evidence/source for reconciliation; no blind copy |
| patched/hb_tep.py, baseline/hb_tep-production-current.py, staging/hb_tep_step5b.py | historical TEP variants | hashburst/tep | archive/reconcile before selecting canonical implementation |
| bin/hb-tep-onboard | TEP enrollment/deployment glue | hashburst/node-installer plus hashburst/tep interface contract | split only after TEP contract freeze |
| docs/TEP_* | deployed TEP operational/protocol documentation | hashburst/tep docs after patent/runtime reconciliation | evidence, not automatically normative |
| ha/ | HA/quorum/lease/fencing | hashburst/tep for protocol/runtime semantics; node-installer for deployment | classify protocol vs deployment before migration |
| hbfiles/ | sovereign storage implementation | future sovereignty component / HashBurst Node integration | retain until sovereignty contract is defined |
| replication/ | storage replication controller/agent | future sovereignty/storage component | retain; no migration before contract freeze |
| aggregator/ | storage/mining aggregation and TEP adapter | component-specific repos after boundary review | retain; split storage vs mining responsibilities |
| ipfs-scripts/ | Kubo/IPFS deployment | hashburst/node-installer | installer-owned deployment logic |
| config/ | deployment examples | node-installer, with component defaults moving to owner repo | gradual split |
| .github/workflows | legacy integration/release CI | each canonical repo plus installer integration CI | retain regressions while new CI is introduced |
| docs/MINING-INTEGRATION-AUDIT.md | mining integration evidence | hashburst/node and mining-accelerator docs as provenance/reference | preserve legacy copy |
| tests/ | cross-version deployment/TEP/HA/replication regression | component repos for unit/contract tests; installer for integration/upgrade | migrate by responsibility, never delete first |

## Rule

The legacy repository remains a reproducible deployment baseline until canonical component releases have equivalent automated tests and a controlled upgrade/rollback path. Migration is copy/verify/adopt first; deletion is a later explicit decision.
