# Architecture decision: identity state

The identity is persistent state external to the replaceable runtime. HashBurst-Node consumes a state path; it does not own lifecycle operations for the private key in dev1.

Canonical production state paths are defined now. An explicit override exists for development, recovery and controlled migration. Existing enrolled identities are never silently moved to the canonical path. A later installer may offer an explicit, verified migration procedure with backup, fingerprint verification and rollback.

`hb-node-state` on the first WSL2 canary remains authoritative for that node during dev1.
