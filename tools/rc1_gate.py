#!/usr/bin/env python3
import json, pathlib, sys
root=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((root/"release/manifest-v0.1.0-rc1.json").read_text())
errors=[]
if m["release"]!="v0.1.0-rc1": errors.append("release mismatch")
if m["production_apply"] is not False: errors.append("production_apply must be false")
if m["mainnet"] is not False: errors.append("mainnet must be false")
a=m["components"]["mining_accelerator"]
if a["mode"]!="shadow" or a["apply_supported"] is not False: errors.append("accelerator is not fail-closed shadow")
e=m["components"]["enrollment"]
if e["sha256"]!="9c6ba3434f5a14dee2bb7bdd8e1b6e87f44418a47e03a0437feda147521ccd73": errors.append("enrollment provenance mismatch")
if not e["source_present_in_rc1"]: errors.append("BLOCKING: exact Enrollment 0.2.0-dev3 source artifact not present")
if errors:
    print("\n".join("FAIL: "+x for x in errors)); sys.exit(1)
print("PASS: RC1 static release gate")
