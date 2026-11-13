# v0.1.0-rc2 conformance matrix

Tagging is forbidden until every mandatory row is PASS. RC1 conformance remains a regression baseline.

| Gate | Requirement | Mandatory |
|---|---|---|
| RC1 regression | RC1 static gate, Enrollment exact ZIP/internal hashes/67 tests | yes |
| RC1 regression | Node dev1-dev4 7/7 | yes |
| RC1 regression | Stage B historical regression, non-shipping | yes |
| RC1 regression | Accelerator 0.1.3 exact provenance and tests | yes |
| RC2 protocol | signed controlled exploration proposal and intent accepted | yes |
| RC2 protocol | tampered proposal rejected before mutation | yes |
| RC2 protocol | tampered intent rejected before mutation | yes |
| RC2 protocol | replay rejected before mutation by persistent journal | yes |
| RC2 binding | changed local binding rejected before mutation | yes |
| RC2 safety | controller cannot enable production_apply | yes |
| RC2 safety | permanent APPLY schema/API absent | yes |
| RC2 watchdog | thermal trip rolls back | yes |
| RC2 watchdog | unhealthy worker rolls back | yes |
| RC2 watchdog | stale telemetry rolls back | yes |
| RC2 watchdog | deadline trip rolls back | yes |
| RC2 watchdog | local watchdog caps cannot be relaxed remotely | yes |
| RC2 recovery | telemetry/runtime exception after mutation rolls back | yes |
| RC2 recovery | successful exploration restores exact baseline | yes |
| RC2 recovery | rollback failure is explicit; never claims baseline restored | yes |
| Receipt | Node-signed terminal receipt binds proposal, intent, pre-state and event log | yes |
| Install | upgrade preserves identity and anti-replay state | yes |
| Install | upgrade preserves exploration/recovery evidence | yes |
| Rollback | executable rollback preserves identity, anti-replay and exploration evidence | yes |
| Rollback | interrupted exploration blocks executable rollback | yes |
| Supply chain | RC1 and RC2 manifests and RC1 CycloneDX SBOM parse | yes |
| Release | mainnet=false and production_apply=false | yes |
