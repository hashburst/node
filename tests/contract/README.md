# Core v1 conformance requirements

A candidate implementation must automatically prove at least:

1. valid signed intent is accepted;
2. invalid signature is rejected;
3. wrong controller is rejected;
4. wrong target node is rejected;
5. expired intent is rejected;
6. replay is rejected persistently;
7. unsupported scope is rejected;
8. unsupported action is rejected;
9. read-only actions produce no forbidden side effects;
10. results are signed by the Node;
11. result binds the exact intent SHA-256;
12. production apply remains disabled in the RC profile.

Experimental exploration additionally requires local provider binding, proposal/action binding, anti-replay before side effects, pre-state capture, thermal and health watchdogs, deterministic rollback, verified baseline restoration and a signed receipt.
