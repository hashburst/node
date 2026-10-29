from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

class IdentityError(RuntimeError): pass

def inspect_public_document(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("kind") != "public" or obj.get("payload", {}).get("role") != "node":
        raise IdentityError("not a HashBurst node public identity document")
    return {
        "node_id": obj.get("key_id"),
        "algorithm": obj.get("algorithm"),
        "scope": obj.get("payload", {}).get("scope"),
        "schema": obj.get("payload", {}).get("schema"),
    }

def inspect_confirmation(path: Path | None) -> dict:
    if not path:
        return {"enrollment_confirmed": False, "confirmation_source": None}
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("schema") != "hb-enrollment-confirmation-v1":
        raise IdentityError("unexpected enrollment confirmation schema")
    return {
        "enrollment_confirmed": bool(obj.get("identity_registry_confirmed")),
        "confirmation_source": str(path),
        "binding_assurance": obj.get("binding_assurance"),
        "worker_binding_present": bool(obj.get("worker_binding_present")),
    }

def enrollment_status(enrollment_python: Path, enrollment_cli: Path, state_path: Path) -> dict:
    cmd = [str(enrollment_python), "-B", str(enrollment_cli), "status", "--state", str(state_path)]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise IdentityError(proc.stderr.strip() or f"Enrollment status failed ({proc.returncode})")
    start = proc.stdout.find("{")
    if start < 0:
        raise IdentityError("Enrollment status returned no JSON")
    try:
        return json.loads(proc.stdout[start:])
    except json.JSONDecodeError as exc:
        raise IdentityError(f"invalid Enrollment status JSON: {exc}") from exc