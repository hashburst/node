from __future__ import annotations
import hashlib,json,os,shutil,subprocess,time,uuid
from pathlib import Path
from .control.crypto import canonical,sign_envelope,verify_envelope,CryptoError

PLAN_SCHEMA='hb-mining-exploration-proposal-v1'
INTENT_SCHEMA='hb-mining-exploration-intent-v1'
RECEIPT_SCHEMA='hb-mining-exploration-receipt-v1'
BINDING_SCHEMA='hb-rainbowminer-binding-v1'
STATES=('received','validated','authorized','prestate_captured','executing','verified','committed','rollback_started','rolled_back','failed')
class ExplorationError(RuntimeError): pass

def sha_bytes(b:bytes): return hashlib.sha256(b).hexdigest()
def sha_file(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def digest(o): return sha_bytes(canonical(o))
def loadj(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def atomic_json(p:Path,o):
 p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex); tmp.write_text(json.dumps(o,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8'); os.replace(tmp,p)

def semantic_profile(payload:dict):
 wl=payload.get('workload') or []
 if len(wl)!=1: raise ExplorationError('profile_requires_single_workload')
 w=wl[0]; alg=w.get('algorithms') or []; pools=w.get('pools') or []; dev=w.get('devices') or []
 if len(alg)!=1 or len(pools)!=1 or len(dev)!=1: raise ExplorationError('profile_semantics_ambiguous')
 return {'hardware':payload.get('hardware'),'profile':payload.get('profile'),'algorithm':alg[0],'miner':w.get('miner'),'pool':pools[0],'miner_version':w.get('version'),'device_name':dev[0].get('name')}

def load_binding(path:Path):
 b=loadj(path)
 if b.get('schema')!=BINDING_SCHEMA: raise ExplorationError('binding_schema_invalid')
 required=('binding_id','node_id','worker_id','hardware','adapter','target')
 if any(not b.get(x) for x in required): raise ExplorationError('binding_incomplete')
 if b['adapter'] not in ('rainbowminer-json-v1','rainbowminer-command-v1'): raise ExplorationError('binding_adapter_denied')
 return b

def build_plan(node_id:str,node_private,binding_path:Path,current:dict,candidate:dict,ttl=300,duration=300,max_temp_c=80,min_samples=6):
 b=load_binding(binding_path); cur=semantic_profile(current); cand=semantic_profile(candidate); now=int(time.time())
 if b['node_id']!=node_id: raise ExplorationError('binding_wrong_node')
 if cur['hardware']!=cand['hardware'] or cur['hardware']!=b['hardware']: raise ExplorationError('hardware_binding_mismatch')
 if cur['algorithm']!=cand['algorithm']: raise ExplorationError('stageB_first_canary_algorithm_change_denied')
 if cur['profile']==cand['profile']: raise ExplorationError('candidate_equals_current')
 allowed=b.get('allowed_profiles',{})
 if cur['profile'] not in allowed or cand['profile'] not in allowed: raise ExplorationError('profile_not_locally_allowlisted')
 action={'binding_id':b['binding_id'],'binding_sha256':sha_file(binding_path),'worker_id':b['worker_id'],'hardware':b['hardware'],'from_profile':cur,'to_profile':cand,'adapter':b['adapter'],'target_id':b['target']}
 action['action_sha256']=digest(action)
 p={'schema':PLAN_SCHEMA,'proposal_id':uuid.uuid4().hex,'node_id':node_id,'created_at':now,'expires_at':now+ttl,'production_apply':False,'exploration_only':True,'one_worker':True,'duration_seconds':duration,'min_samples':min_samples,'max_temperature_c':max_temp_c,'candidate_action':action}
 return sign_envelope('mining-exploration-proposal',PLAN_SCHEMA,node_id,node_private,p)

def make_apply_intent(controller_id:str,controller_private,node_id:str,proposal_env:dict,ttl=180):
 p=proposal_env.get('payload',{}); now=int(time.time())
 if p.get('schema')!=PLAN_SCHEMA or p.get('node_id')!=node_id: raise ExplorationError('proposal_binding_mismatch')
 body={'schema':INTENT_SCHEMA,'intent_id':uuid.uuid4().hex,'controller_id':controller_id,'node_id':node_id,'issued_at':now,'expires_at':min(now+ttl,p['expires_at']),'proposal_id':p['proposal_id'],'proposal_sha256':digest(proposal_env),'candidate_action_sha256':p['candidate_action']['action_sha256'],'scope':'mining-exploration-one-worker','production_apply':True}
 return sign_envelope('mining-exploration-intent',INTENT_SCHEMA,controller_id,controller_private,body)

def _event(log:Path,state:str,detail=None):
 if state not in STATES: raise ExplorationError('invalid_state')
 rec={'at':int(time.time()),'state':state,'detail':detail or {}}
 with log.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,sort_keys=True,separators=(',',':'))+'\n'); f.flush(); os.fsync(f.fileno())

def _validate_command_binding(b,profile):
 spec=b['allowed_profiles'][profile]; argv=spec.get('argv')
 if not isinstance(argv,list) or not argv or not all(isinstance(x,str) for x in argv): raise ExplorationError('argv_invalid')
 exe=Path(argv[0]).resolve(strict=True); expected=spec.get('executable_sha256')
 if not expected or sha_file(exe)!=expected: raise ExplorationError('executable_hash_mismatch')
 return argv

def _capture(b):
 if b['adapter']=='rainbowminer-json-v1':
  p=Path(b['target']).resolve(strict=True); raw=p.read_bytes(); return {'target':str(p),'sha256':sha_bytes(raw),'bytes_hex':raw.hex()}
 prof=b.get('current_profile')
 if not prof: raise ExplorationError('current_profile_missing')
 return {'current_profile':prof}

def _apply(b,profile):
 spec=b['allowed_profiles'][profile]
 if b['adapter']=='rainbowminer-json-v1':
  p=Path(b['target']).resolve(strict=True); expected=spec.get('document')
  if not isinstance(expected,dict): raise ExplorationError('profile_document_invalid')
  atomic_json(p,expected); return {'target_sha256':sha_file(p)}
 argv=_validate_command_binding(b,profile)
 cp=subprocess.run(argv,capture_output=True,text=True,timeout=int(spec.get('timeout_seconds',60)),shell=False)
 if cp.returncode: raise ExplorationError('rainbowminer_transition_failed')
 return {'returncode':cp.returncode,'stdout_sha256':sha_bytes(cp.stdout.encode()),'stderr_sha256':sha_bytes(cp.stderr.encode())}

def _restore(b,pre):
 if b['adapter']=='rainbowminer-json-v1':
  p=Path(pre['target']); raw=bytes.fromhex(pre['bytes_hex']); tmp=p.with_name(p.name+'.rollback-'+uuid.uuid4().hex); tmp.write_bytes(raw); os.replace(tmp,p)
  if sha_file(p)!=pre['sha256']: raise ExplorationError('rollback_verification_failed')
 else: _apply(b,pre['current_profile'])

def execute_exploration(node_id,node_private,node_public_key,controller_id,controller_public_key,proposal_env,intent_env,binding_path:Path,runtime_dir:Path,telemetry_reader,sleep=time.sleep):
 now=int(time.time()); p=verify_envelope(proposal_env,'mining-exploration-proposal',node_public_key,node_id); i=verify_envelope(intent_env,'mining-exploration-intent',controller_public_key,controller_id)
 eid=i.get('intent_id') or uuid.uuid4().hex; run=runtime_dir/('explore-'+eid); run.mkdir(parents=True,exist_ok=False); log=run/'events.jsonl'; _event(log,'received')
 b=load_binding(binding_path)
 try:
  if p.get('schema')!=PLAN_SCHEMA or i.get('schema')!=INTENT_SCHEMA: raise ExplorationError('schema_mismatch')
  if p.get('node_id')!=node_id or i.get('node_id')!=node_id or i.get('controller_id')!=controller_id: raise ExplorationError('identity_binding_mismatch')
  if p.get('expires_at',0)<now or i.get('expires_at',0)<now: raise ExplorationError('expired')
  if i.get('proposal_id')!=p.get('proposal_id') or i.get('proposal_sha256')!=digest(proposal_env): raise ExplorationError('proposal_reference_mismatch')
  a=p['candidate_action']
  if i.get('candidate_action_sha256')!=a.get('action_sha256') or digest({k:v for k,v in a.items() if k!='action_sha256'})!=a.get('action_sha256'): raise ExplorationError('candidate_action_hash_mismatch')
  if sha_file(binding_path)!=a.get('binding_sha256') or b['binding_id']!=a['binding_id'] or b['worker_id']!=a['worker_id'] or b['hardware']!=a['hardware']: raise ExplorationError('local_binding_changed')
  _event(log,'validated'); _event(log,'authorized')
  pre=_capture(b); atomic_json(run/'pre-state.json',pre); _event(log,'prestate_captured',{'prestate_sha256':digest(pre)})
  _event(log,'executing'); _apply(b,a['to_profile']['profile'])
  samples=[]; deadline=time.monotonic()+p['duration_seconds']; thermal_trip=False; health_trip=False
  while len(samples)<p['min_samples'] or time.monotonic()<deadline:
   s=telemetry_reader(b['worker_id']); samples.append(s); atomic_json(run/'last-telemetry.json',s)
   temp=s.get('temperature_c'); healthy=s.get('healthy')
   if not isinstance(temp,(int,float)) or temp>p['max_temperature_c']: thermal_trip=True; raise ExplorationError('thermal_watchdog_trip')
   if healthy is not True: health_trip=True; raise ExplorationError('health_watchdog_trip')
   if len(samples)>=p['min_samples'] and time.monotonic()>=deadline: break
   sleep(min(15,max(0,p['duration_seconds']/max(1,p['min_samples']))))
  _event(log,'verified',{'samples':len(samples),'temperature_c_max':max(x['temperature_c'] for x in samples)})
  _event(log,'rollback_started',{'reason':'exploration_complete_restore_baseline'}); _restore(b,pre); _event(log,'rolled_back'); _event(log,'committed')
  outcome='completed_restored'
 except Exception as e:
  try:
   if 'pre' in locals(): _event(log,'rollback_started',{'reason':str(e)}); _restore(b,pre); _event(log,'rolled_back')
  except Exception as re: _event(log,'failed',{'error':str(e),'rollback_error':str(re)}); raise ExplorationError('rollback_failed') from re
  _event(log,'failed',{'error':str(e)}); outcome='aborted_restored'
  error=str(e)
 receipt={'schema':RECEIPT_SCHEMA,'exploration_id':eid,'proposal_id':p.get('proposal_id'),'node_id':node_id,'controller_id':controller_id,'finished_at':int(time.time()),'outcome':outcome,'error':locals().get('error'),'samples':len(locals().get('samples',[])),'thermal_trip':locals().get('thermal_trip',False),'health_trip':locals().get('health_trip',False),'event_log_sha256':sha_file(log),'production_apply':False,'baseline_restored':True}
 env=sign_envelope('mining-exploration-receipt',RECEIPT_SCHEMA,node_id,node_private,receipt); atomic_json(run/'receipt.signed.json',env); return env