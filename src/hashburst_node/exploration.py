from __future__ import annotations
import hashlib,json,os,subprocess,time,uuid
from pathlib import Path
from .control.crypto import canonical,sign_envelope,verify_envelope,CryptoError
from .control.journal import consume,ReplayError

PROPOSAL_SCHEMA='hb-mining-exploration-proposal-v1'
INTENT_SCHEMA='hb-mining-exploration-intent-v1'
RECEIPT_SCHEMA='hb-mining-exploration-receipt-v1'
BINDING_SCHEMA='hb-rainbowminer-binding-v1'
SCOPE='mining-controlled-exploration'
STATES=('received','validated','authorized','prestate_captured','executing','verified','rollback_started','rolled_back','committed','failed')
class ExplorationError(RuntimeError): pass
class RollbackError(ExplorationError): pass

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def digest(o): return sha_bytes(canonical(o))
def loadj(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def atomic_json(p,o):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex)
 t.write_text(json.dumps(o,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8'); os.replace(t,p)

def semantic_profile(payload):
 wl=payload.get('workload') or []
 if len(wl)!=1: raise ExplorationError('profile_requires_single_workload')
 w=wl[0]; alg=w.get('algorithms') or []; pools=w.get('pools') or []; dev=w.get('devices') or []
 if len(alg)!=1 or len(pools)!=1 or len(dev)!=1: raise ExplorationError('profile_semantics_ambiguous')
 return {'hardware':payload.get('hardware'),'profile':payload.get('profile'),'algorithm':alg[0],'miner':w.get('miner'),'pool':pools[0],'miner_version':w.get('version'),'device_name':dev[0].get('name')}

def load_binding(path):
 b=loadj(path)
 if b.get('schema')!=BINDING_SCHEMA: raise ExplorationError('binding_schema_invalid')
 if any(not b.get(x) for x in ('binding_id','node_id','worker_id','hardware','adapter','target')): raise ExplorationError('binding_incomplete')
 if b['adapter'] not in ('rainbowminer-json-v1','rainbowminer-command-v1'): raise ExplorationError('binding_adapter_denied')
 pol=b.get('watchdog_policy') or {}
 for k in ('max_temperature_c','max_duration_seconds','max_telemetry_age_seconds'):
  if k not in pol or not isinstance(pol[k],(int,float)) or pol[k]<=0: raise ExplorationError('watchdog_policy_incomplete')
 return b

def build_proposal(node_id,node_private,binding_path,current,candidate,ttl=300,duration=300,max_temp_c=80,max_telemetry_age=30,min_samples=6):
 b=load_binding(binding_path); cur=semantic_profile(current); cand=semantic_profile(candidate); now=int(time.time())
 if b['node_id']!=node_id: raise ExplorationError('binding_wrong_node')
 if cur['hardware']!=cand['hardware'] or cur['hardware']!=b['hardware']: raise ExplorationError('hardware_binding_mismatch')
 if cur['algorithm']!=cand['algorithm']: raise ExplorationError('algorithm_change_denied')
 if cur['profile']==cand['profile']: raise ExplorationError('candidate_equals_current')
 if cur['profile'] not in b.get('allowed_profiles',{}) or cand['profile'] not in b.get('allowed_profiles',{}): raise ExplorationError('profile_not_locally_allowlisted')
 pol=b['watchdog_policy']
 effective={'max_temperature_c':min(max_temp_c,pol['max_temperature_c']),'duration_seconds':min(duration,pol['max_duration_seconds']),'max_telemetry_age_seconds':min(max_telemetry_age,pol['max_telemetry_age_seconds']),'min_samples':max(1,int(min_samples))}
 action={'binding_id':b['binding_id'],'binding_sha256':sha_file(binding_path),'worker_id':b['worker_id'],'hardware':b['hardware'],'from_profile':cur,'to_profile':cand,'adapter':b['adapter'],'target_id':b['target']}
 action['action_sha256']=digest(action)
 p={'schema':PROPOSAL_SCHEMA,'proposal_id':uuid.uuid4().hex,'node_id':node_id,'created_at':now,'expires_at':now+ttl,'scope':SCOPE,'production_apply':False,'exploration_only':True,'one_worker':True,'watchdog':effective,'candidate_action':action}
 return sign_envelope('mining-exploration-proposal',PROPOSAL_SCHEMA,node_id,node_private,p)

def make_intent(controller_id,controller_private,node_id,proposal_env,ttl=180):
 p=proposal_env.get('payload',{}); now=int(time.time())
 if p.get('schema')!=PROPOSAL_SCHEMA or p.get('node_id')!=node_id or p.get('production_apply') is not False: raise ExplorationError('proposal_binding_mismatch')
 body={'schema':INTENT_SCHEMA,'intent_id':uuid.uuid4().hex,'controller_id':controller_id,'node_id':node_id,'issued_at':now,'expires_at':min(now+ttl,p['expires_at']),'proposal_id':p['proposal_id'],'proposal_sha256':digest(proposal_env),'candidate_action_sha256':p['candidate_action']['action_sha256'],'scope':SCOPE,'production_apply':False}
 return sign_envelope('mining-exploration-intent',INTENT_SCHEMA,controller_id,controller_private,body)

def _event(log,state,detail=None):
 if state not in STATES: raise ExplorationError('invalid_state')
 with Path(log).open('a',encoding='utf-8') as f:
  f.write(json.dumps({'at':int(time.time()),'state':state,'detail':detail or {}},sort_keys=True,separators=(',',':'))+'\n'); f.flush(); os.fsync(f.fileno())

def _capture(b):
 if b['adapter']=='rainbowminer-json-v1':
  p=Path(b['target']).resolve(strict=True); raw=p.read_bytes(); return {'adapter':b['adapter'],'target':str(p),'sha256':sha_bytes(raw),'bytes_hex':raw.hex()}
 prof=b.get('current_profile')
 if not prof: raise ExplorationError('current_profile_missing')
 return {'adapter':b['adapter'],'current_profile':prof}

def _validate_command(b,profile):
 spec=b['allowed_profiles'][profile]; argv=spec.get('argv')
 if not isinstance(argv,list) or not argv or not all(isinstance(x,str) for x in argv): raise ExplorationError('argv_invalid')
 exe=Path(argv[0]).resolve(strict=True)
 if sha_file(exe)!=spec.get('executable_sha256'): raise ExplorationError('executable_hash_mismatch')
 return argv,spec

def _apply(b,profile):
 spec=b['allowed_profiles'][profile]
 if b['adapter']=='rainbowminer-json-v1':
  doc=spec.get('document')
  if not isinstance(doc,dict): raise ExplorationError('profile_document_invalid')
  atomic_json(Path(b['target']).resolve(strict=True),doc); return
 argv,spec=_validate_command(b,profile)
 cp=subprocess.run(argv,capture_output=True,text=True,timeout=int(spec.get('timeout_seconds',60)),shell=False)
 if cp.returncode: raise ExplorationError('rainbowminer_transition_failed')

def _restore_and_verify(b,pre):
 if b['adapter']=='rainbowminer-json-v1':
  p=Path(pre['target']); t=p.with_name(p.name+'.rollback-'+uuid.uuid4().hex); t.write_bytes(bytes.fromhex(pre['bytes_hex'])); os.replace(t,p)
  if sha_file(p)!=pre['sha256']: raise RollbackError('rollback_verification_failed')
 else:
  _apply(b,pre['current_profile'])
  if b.get('current_profile_probe') is None: raise RollbackError('rollback_probe_missing')
  argv=b['current_profile_probe']; cp=subprocess.run(argv,capture_output=True,text=True,timeout=30,shell=False)
  if cp.returncode or cp.stdout.strip()!=pre['current_profile']: raise RollbackError('rollback_verification_failed')

def _validate_signed(node_id,node_public,controller_id,controller_public,proposal_env,intent_env,binding_path,now):
 p=verify_envelope(proposal_env,'mining-exploration-proposal',node_public,node_id)
 i=verify_envelope(intent_env,'mining-exploration-intent',controller_public,controller_id)
 if p.get('schema')!=PROPOSAL_SCHEMA or i.get('schema')!=INTENT_SCHEMA: raise ExplorationError('schema_mismatch')
 if p.get('production_apply') is not False or i.get('production_apply') is not False: raise ExplorationError('production_apply_denied')
 if p.get('scope')!=SCOPE or i.get('scope')!=SCOPE: raise ExplorationError('scope_denied')
 if p.get('node_id')!=node_id or i.get('node_id')!=node_id or i.get('controller_id')!=controller_id: raise ExplorationError('identity_binding_mismatch')
 if p.get('expires_at',0)<now or i.get('expires_at',0)<now or i.get('issued_at',now+31)>now+30: raise ExplorationError('expired_or_not_yet_valid')
 if i.get('proposal_id')!=p.get('proposal_id') or i.get('proposal_sha256')!=digest(proposal_env): raise ExplorationError('proposal_reference_mismatch')
 a=p['candidate_action']
 if i.get('candidate_action_sha256')!=a.get('action_sha256') or digest({k:v for k,v in a.items() if k!='action_sha256'})!=a.get('action_sha256'): raise ExplorationError('candidate_action_hash_mismatch')
 b=load_binding(binding_path)
 if sha_file(binding_path)!=a.get('binding_sha256') or b['binding_id']!=a['binding_id'] or b['worker_id']!=a['worker_id'] or b['hardware']!=a['hardware']: raise ExplorationError('local_binding_changed')
 return p,i,b

def execute(node_id,node_private,node_public,controller_id,controller_public,proposal_env,intent_env,binding_path,runtime_dir,replay_db,telemetry_reader,sleep=time.sleep,clock=time.time,monotonic=time.monotonic,restore_fn=None):
 now=int(clock()); eid=(intent_env.get('payload') or {}).get('intent_id') or uuid.uuid4().hex; run=Path(runtime_dir)/('explore-'+eid); run.mkdir(parents=True,exist_ok=False); log=run/'events.jsonl'; _event(log,'received')
 p={}; i={}; pre=None; samples=[]; trip=None; baseline_restored=False; outcome='rejected'; error=None
 try:
  p,i,b=_validate_signed(node_id,node_public,controller_id,controller_public,proposal_env,intent_env,binding_path,now); _event(log,'validated')
  consume(Path(replay_db),i['intent_id'],digest(intent_env)); _event(log,'authorized')
  pre=_capture(b); atomic_json(run/'pre-state.json',pre); pre_digest=digest(pre); _event(log,'prestate_captured',{'prestate_sha256':pre_digest})
  _event(log,'executing'); _apply(b,p['candidate_action']['to_profile']['profile'])
  wd=p['watchdog']; started=monotonic(); deadline=started+wd['duration_seconds']
  while True:
   current=monotonic()
   if current>deadline and len(samples)<wd['min_samples']: trip='deadline'; raise ExplorationError('deadline_watchdog_trip')
   s=telemetry_reader(b['worker_id']); samples.append(s); atomic_json(run/'last-telemetry.json',s)
   temp=s.get('temperature_c'); healthy=s.get('healthy'); sampled_at=s.get('sampled_at')
   if not isinstance(temp,(int,float)) or temp>wd['max_temperature_c']: trip='thermal'; raise ExplorationError('thermal_watchdog_trip')
   if healthy is not True: trip='health'; raise ExplorationError('health_watchdog_trip')
   if not isinstance(sampled_at,(int,float)) or clock()-sampled_at>wd['max_telemetry_age_seconds'] or sampled_at>clock()+5: trip='staleness'; raise ExplorationError('telemetry_staleness_watchdog_trip')
   if len(samples)>=wd['min_samples'] and current>=deadline: break
   sleep(min(1,max(0,deadline-current)))
  _event(log,'verified',{'samples':len(samples)})
  _event(log,'rollback_started',{'reason':'exploration_complete_restore_baseline'})
  (restore_fn or _restore_and_verify)(b,pre); baseline_restored=True; _event(log,'rolled_back'); _event(log,'committed'); outcome='completed_restored'
 except ReplayError as e:
  error='replay_detected'; _event(log,'failed',{'error':error})
 except Exception as e:
  error=str(e)
  if pre is not None:
   try:
    _event(log,'rollback_started',{'reason':error}); (restore_fn or _restore_and_verify)(b,pre); baseline_restored=True; _event(log,'rolled_back'); outcome='aborted_restored'
   except Exception as re:
    baseline_restored=False; outcome='rollback_failed'; error=error+'; rollback_error='+str(re); _event(log,'failed',{'error':error})
  if outcome!='rollback_failed': _event(log,'failed',{'error':error})
 receipt={'schema':RECEIPT_SCHEMA,'exploration_id':eid,'proposal_id':p.get('proposal_id'),'proposal_sha256':digest(proposal_env),'intent_sha256':digest(intent_env),'prestate_sha256':digest(pre) if pre else None,'node_id':node_id,'controller_id':controller_id,'finished_at':int(clock()),'outcome':outcome,'error':error,'samples':len(samples),'watchdog_trip':trip,'event_log_sha256':sha_file(log),'scope':SCOPE,'production_apply':False,'baseline_restored':baseline_restored}
 env=sign_envelope('mining-exploration-receipt',RECEIPT_SCHEMA,node_id,node_private,receipt); atomic_json(run/'receipt.signed.json',env); return env
