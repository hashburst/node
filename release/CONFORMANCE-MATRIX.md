# v0.1.0-rc1 conformance matrix

Tagging is forbidden until every mandatory row is PASS.

| Gate | Requirement | Mandatory |
|---|---|---|
| Provenance | Node verified exact blobs | yes |
| Provenance | Enrollment 0.2.0-dev3 exact ZIP SHA-256 and source present | yes |
| Provenance | Accelerator 0.1.3 verified exact blobs | yes |
| Unit | Node dev1-dev4 7/7 | yes |
| Unit | Stage B regression 11/11 (non-shipping experimental code) | yes |
| Unit | Enrollment dev3 67/67 | yes |
| Unit | Accelerator 0.1.3 11/11 | yes |
| Protocol | valid signed intent accepted | yes |
| Protocol | invalid signature rejected | yes |
| Protocol | wrong controller rejected | yes |
| Protocol | wrong node rejected | yes |
| Protocol | expired intent rejected | yes |
| Protocol | replay rejected before side effect | yes |
| Protocol | unsupported scope rejected | yes |
| Protocol | unsupported action rejected | yes |
| Safety | read-only actions have no forbidden side effects | yes |
| Safety | result is Node-signed and binds exact intent digest | yes |
| Safety | production_apply=false everywhere | yes |
| Safety | Accelerator mode=shadow and apply_supported=false | yes |
| Install | clean install preserves external identity state boundary | yes |
| Upgrade | install never recreates anti-replay DB | yes |
| Rollback | executable rollback preserves identity and anti-replay state | yes |
| Supply chain | release manifest and CycloneDX SBOM validate | yes |
| Release | no mainnet enablement | yes |

Stage B is regression evidence only and is not part of the RC1 runtime payload.
