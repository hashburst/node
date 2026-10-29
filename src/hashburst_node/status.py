from __future__ import annotations
import json, platform
from pathlib import Path
from .paths import resolve_state_path, canonical_state_path
from .core.identity_adapter import inspect_public_document, inspect_confirmation, enrollment_status, IdentityError

VERSION="0.1.0-dev2"

def build_status(args) -> dict:
    state, source = resolve_state_path(args.state_path, args.config_state_path)
    public = inspect_public_document(Path(args.node_public))
    confirmation = inspect_confirmation(Path(args.enrollment_confirmation) if args.enrollment_confirmation else None)
    if not state.is_dir():
        raise IdentityError(f"identity state directory does not exist: {state}")
    live = None
    if args.enrollment_cli:
        py = Path(args.enrollment_python) if args.enrollment_python else Path(platform.python_implementation() and __import__('sys').executable)
        live = enrollment_status(py, Path(args.enrollment_cli), state)
        if live.get("public_fingerprint") != public.get("node_id"):
            raise IdentityError("state/public fingerprint mismatch")
    return {
      "schema":"hb-node-runtime-status-v1", "runtime":"HashBurst-Node", "version":VERSION,
      "node_id": public["node_id"],
      "identity": {"state_path":str(state), "state_path_source":source, "canonical_state_path":str(canonical_state_path()),
                   "using_canonical_path": state == canonical_state_path(), "persistent": bool(live.get("identity_persistent")) if live else None,
                   "encrypted": bool(live.get("private_key_encrypted")) if live else None,
                   **confirmation},
      "capabilities":{"tep":False,"bi3339m_mining":False,"ai_compute":False,"storage":False},
      "control_plane":{"signed_intents":False,"production_apply":False},
      "safety":{"network_calls":0,"miner_configuration_modified":False,"history_or_policy_modified":False},
      "platform":{"system":platform.system(),"release":platform.release()},
    }

def dumps(status: dict) -> str: return json.dumps(status, indent=2, sort_keys=False)
