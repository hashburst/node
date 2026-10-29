from __future__ import annotations
import hashlib, json, time, uuid
from pathlib import Path
from .crypto import canonical, load_matching_private, load_public_doc, sign_envelope, verify_envelope, CryptoError
from .journal import consume, ReplayError
from ..mining_adapter import capabilities as mining_capabilities, status as mining_status, telemetry_snapshot, shadow as mining_shadow, MiningError
from ..planning import build_signed_proposal

ALLOWED_ACTIONS={"probe.status","probe.capabilities","mining.status","mining.telemetry.snapshot","mining.accelerator.shadow","mining.predict.decide"}
SCOPE="control-read-only"

def write_json(path: Path, obj: dict):
    if path.exists(): raise RuntimeError(f"refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")

def make_intent(state, controller_public, node_public, out, action="probe.status", ttl=300):
    cid,key=load_matching_private(state,controller_public,"controller"); nid,_=load_public_doc(node_public,"node")
    now=int(time.time()); payload={"schema":"hb-control-intent-v1","intent_id":uuid.uuid4().hex,"controller_id":cid,"node_id":nid,"issued_at":now,"expires_at":now+ttl,"scope":SCOPE,"action":action,"parameters":{},"production_apply":False}
    env=sign_envelope("intent","hb-control-intent-v1",cid,key,payload); write_json(out,env); return env

def process_intent(state,node_public,controller_public,intent_file,journal,out,accelerator_root=None,runtime_dir=None):
    nid,npriv=load_matching_private(state,node_public,"node"); cid,cpub=load_public_doc(controller_public,"controller")
    raw=intent_file.read_bytes(); ih=hashlib.sha256(raw).hexdigest(); obj=json.loads(raw); result="ACK"; reason="accepted_read_only_probe"; intent_id=None; action=None; observation=None
    try:
        p=verify_envelope(obj,"intent",cpub,cid); intent_id=p.get("intent_id")
        now=int(time.time())
        if p.get("schema")!="hb-control-intent-v1": raise ValueError("schema_mismatch")
        if p.get("controller_id")!=cid: raise ValueError("controller_mismatch")
        if p.get("node_id")!=nid: raise ValueError("wrong_target_node")
        if p.get("scope")!=SCOPE: raise ValueError("scope_denied")
        if p.get("production_apply") is not False: raise ValueError("production_apply_denied")
        action=p.get("action")
        if action not in ALLOWED_ACTIONS: raise ValueError("action_denied")
        if not isinstance(p.get("issued_at"),int) or not isinstance(p.get("expires_at"),int) or p["issued_at"]>now+30 or p["expires_at"]<now: raise ValueError("intent_expired_or_not_yet_valid")
        consume(journal,intent_id,ih)
        if action=="probe.capabilities":
            if accelerator_root is None: raise ValueError("accelerator_root_required")
            observation=mining_capabilities(accelerator_root); reason="accepted_capability_probe"
        elif action=="mining.status":
            if accelerator_root is None: raise ValueError("accelerator_root_required")
            observation=mining_status(accelerator_root); reason="accepted_mining_status"
        elif action=="mining.telemetry.snapshot":
            if accelerator_root is None: raise ValueError("accelerator_root_required")
            observation=telemetry_snapshot(accelerator_root); reason="accepted_telemetry_snapshot"
        elif action=="mining.accelerator.shadow":
            if accelerator_root is None or runtime_dir is None: raise ValueError("accelerator_runtime_required")
            observation=mining_shadow(accelerator_root,runtime_dir); reason="accepted_shadow_evaluation"
        elif action=="mining.predict.decide":
            if accelerator_root is None or runtime_dir is None: raise ValueError("accelerator_runtime_required")
            observation=build_signed_proposal(accelerator_root,runtime_dir,nid,npriv); reason="accepted_predict_decide"
    except ReplayError:
        result="NACK"; reason="replay_detected"
    except (CryptoError,MiningError,ValueError,KeyError,TypeError) as e:
        result="NACK"; reason=str(e)
    payload={"schema":"hb-control-result-v1","intent_id":intent_id,"intent_sha256":ih,"controller_id":cid,"node_id":nid,"processed_at":int(time.time()),"result":result,"reason":reason,"scope":SCOPE,"action":action or "unknown","production_apply":False,"network_calls":0,"miner_configuration_modified":False,"history_or_policy_modified":False,"observation":observation}
    env=sign_envelope("result","hb-control-result-v1",nid,npriv,payload); write_json(out,env); return env

def verify_result(controller_public,node_public,result_file):
    cid,_=load_public_doc(controller_public,"controller"); nid,npub=load_public_doc(node_public,"node")
    obj=json.loads(result_file.read_text(encoding="utf-8")); p=verify_envelope(obj,"result",npub,nid)
    if p.get("controller_id")!=cid or p.get("node_id")!=nid: raise CryptoError("result identity binding mismatch")
    return p
