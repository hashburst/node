from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .status import build_status, dumps
from .core.identity_adapter import IdentityError
from .control.crypto import CryptoError
from .control.protocol import make_intent, process_intent, verify_result
from .control.crypto import load_public_doc
from .planning import verify_proposal

def parser():
    p=argparse.ArgumentParser(prog="hb-node",description="HashBurst Node Runtime")
    s=p.add_subparsers(dest="command",required=True)
    q=s.add_parser("status",help="read-only node runtime status")
    q.add_argument("--state-path"); q.add_argument("--config-state-path"); q.add_argument("--node-public",required=True); q.add_argument("--enrollment-confirmation"); q.add_argument("--enrollment-cli"); q.add_argument("--enrollment-python")
    q=s.add_parser("intent-create",help="controller: create signed read-only intent")
    q.add_argument("--state",required=True); q.add_argument("--controller-public",required=True); q.add_argument("--node-public",required=True); q.add_argument("--out",required=True); q.add_argument("--action",default="probe.status",choices=["probe.status","probe.capabilities","mining.status","mining.telemetry.snapshot","mining.accelerator.shadow","mining.predict.decide"]); q.add_argument("--ttl",type=int,default=300)
    q=s.add_parser("intent-process",help="node: verify intent, enforce policy/anti-replay, sign ACK/NACK")
    q.add_argument("--state",required=True); q.add_argument("--node-public",required=True); q.add_argument("--controller-public",required=True); q.add_argument("--intent",required=True); q.add_argument("--journal",required=True); q.add_argument("--out",required=True); q.add_argument("--accelerator-root"); q.add_argument("--runtime-dir")
    q=s.add_parser("result-verify",help="controller: verify signed node ACK/NACK")
    q.add_argument("--controller-public",required=True); q.add_argument("--node-public",required=True); q.add_argument("--result",required=True)
    q=s.add_parser("proposal-verify",help="verify a signed dev4 mining proposal")
    q.add_argument("--node-public",required=True); q.add_argument("--proposal",required=True)
    return p

def main():
    a=parser().parse_args()
    try:
        if a.command=="status": print(dumps(build_status(a))); return 0
        if a.command=="intent-create":
            o=make_intent(Path(a.state),Path(a.controller_public),Path(a.node_public),Path(a.out),a.action,a.ttl); print(json.dumps(o["payload"],indent=2)); print(f"OUTPUT={a.out}"); return 0
        if a.command=="intent-process":
            o=process_intent(Path(a.state),Path(a.node_public),Path(a.controller_public),Path(a.intent),Path(a.journal),Path(a.out),Path(a.accelerator_root) if a.accelerator_root else None,Path(a.runtime_dir) if a.runtime_dir else None); print(json.dumps(o["payload"],indent=2)); print(f"OUTPUT={a.out}"); return 0 if o["payload"]["result"]=="ACK" else 3
        if a.command=="result-verify": print(json.dumps(verify_result(Path(a.controller_public),Path(a.node_public),Path(a.result)),indent=2)); return 0
        if a.command=="proposal-verify":
            nid,npub=load_public_doc(Path(a.node_public),"node"); print(json.dumps(verify_proposal(npub,nid,Path(a.proposal)),indent=2)); return 0
    except (IdentityError,CryptoError,OSError,ValueError,RuntimeError) as e:
        print(f"HB_NODE_ERROR: {e}",file=sys.stderr); return 2
    return 1
if __name__=="__main__": raise SystemExit(main())