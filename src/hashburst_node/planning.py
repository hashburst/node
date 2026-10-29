from __future__ import annotations
import hashlib, json, sqlite3, time, uuid
from contextlib import closing
from pathlib import Path
from .control.crypto import canonical, sign_envelope, verify_envelope, CryptoError
from .mining_adapter import baseline, unchanged, status, telemetry_snapshot, shadow, sha, MiningError

SCHEMA='hb-mining-proposal-v1'

def _health(root:Path, now:int, max_age:int):
    dbp=root/'history.sqlite'; uri=dbp.as_uri()+'?mode=ro&immutable=1'
    with closing(sqlite3.connect(uri,uri=True,timeout=5)) as db:
        db.execute('PRAGMA query_only=ON'); db.execute('PRAGMA trusted_schema=OFF')
        rows=db.execute('SELECT collected,healthy FROM worker_health').fetchall()
    healthy=sum(1 for t,h in rows if h and -30 <= now-t <= max_age)
    stale=sum(1 for t,h in rows if h and now-t > max_age)
    unhealthy=sum(1 for _,h in rows if not h)
    return {'records_total':len(rows),'healthy_fresh':healthy,'healthy_stale':stale,'unhealthy':unhealthy}

def build_signed_proposal(root:Path,runtime_dir:Path,node_id:str,node_private,ttl:int=300):
    root,b=baseline(root); now=int(time.time())
    st=status(root); snap=telemetry_snapshot(root); sh=shadow(root,runtime_dir)
    health=_health(root,now,st['policy']['max_age_seconds']); unchanged(root,b)
    newest=snap.get('newest_sample_at'); max_age=st['policy']['max_age_seconds']
    freshness_ok=isinstance(newest,int) and -30 <= now-newest <= max_age
    thermal_ok=isinstance(snap.get('temperature_c_max'),(int,float)) and snap['temperature_c_max'] <= json.loads((root/'policy.json').read_text(encoding='utf-8'))['max_temperature_c']
    health_ok=health['records_total']>0 and health['healthy_fresh']==health['records_total']
    economics_ok=st['policy']['economics_usable'] is True
    gates={'freshness':{'pass':freshness_ok,'newest_sample_at':newest,'max_age_seconds':max_age},
           'thermal':{'pass':thermal_ok,'temperature_c_max':snap.get('temperature_c_max'),'max_temperature_c':json.loads((root/'policy.json').read_text(encoding='utf-8'))['max_temperature_c']},
           'health':{'pass':health_ok,**health},
           'economics':{'pass':economics_ok,'price_state':st['policy']['price_state'],'price_observed_at':st['policy']['price_observed_at']}}
    gates_pass=all(x['pass'] for x in gates.values())
    decision='eligible_shadow_decisions' if gates_pass and sh['decisions_total']>0 else 'blocked'
    reasons=[k for k,v in gates.items() if not v['pass']]
    if gates_pass and sh['decisions_total']==0: reasons.append('no_supported_decision')
    payload={'schema':SCHEMA,'proposal_id':uuid.uuid4().hex,'node_id':node_id,'created_at':now,'expires_at':now+ttl,
             'mode':'shadow','production_apply':False,'apply_supported':False,'decision':decision,'block_reasons':reasons,
             'gates':gates,'shadow':{'proposal_sha256':sh['proposal_sha256'],'decision_counts':sh['decision_counts'],'decisions_total':sh['decisions_total']},
             'provenance':{'accelerator_version':'0.1.2','accelerator_py_sha256':b['accelerator.py'],'policy_sha256':b['policy.json'],'history_sha256':b['history.sqlite'],'telemetry_schema':snap['schema'],'telemetry_source':snap['source'],'newest_sample_at':newest}}
    env=sign_envelope('mining-proposal',SCHEMA,node_id,node_private,payload)
    runtime_dir.mkdir(parents=True,exist_ok=True); out=runtime_dir/f"proposal-{payload['proposal_id']}.signed.json"
    out.write_text(json.dumps(env,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    unchanged(root,b)
    return {'schema':'hb-node-mining-plan-result-v1','proposal_file':str(out),'proposal_sha256':sha(out),'proposal':payload}

def verify_proposal(node_public_key,node_id:str,proposal_file:Path,now:int|None=None):
    obj=json.loads(proposal_file.read_text(encoding='utf-8')); p=verify_envelope(obj,'mining-proposal',node_public_key,node_id)
    now=int(time.time()) if now is None else now
    if p.get('schema')!=SCHEMA or p.get('node_id')!=node_id: raise CryptoError('proposal_binding_mismatch')
    if p.get('production_apply') is not False or p.get('apply_supported') is not False: raise CryptoError('proposal_apply_contract_mismatch')
    if not isinstance(p.get('expires_at'),int) or p['expires_at']<now: raise CryptoError('proposal_expired')
    return p