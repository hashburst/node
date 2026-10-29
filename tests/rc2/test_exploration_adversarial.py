import copy,json,tempfile,time,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from hashburst_node.exploration import *

class Clock:
 def __init__(self): self.wall=2000000000.0; self.mono=100.0
 def time(self): return self.wall
 def monotonic(self): return self.mono
 def sleep(self,n): self.wall+=n; self.mono+=n

class RC2Adversarial(unittest.TestCase):
 def setUp(self):
  self.nk=Ed25519PrivateKey.generate(); self.ck=Ed25519PrivateKey.generate(); self.clock=Clock()
  self.td=tempfile.TemporaryDirectory(); self.root=Path(self.td.name); self.cfg=self.root/'worker.json'; self.original=b'{"profile":"A"}\n'; self.cfg.write_bytes(self.original)
  hw='h'*64
  self.a={'hardware':hw,'profile':'A','workload':[{'algorithms':['RandomX'],'devices':[{'name':'CPU'}],'miner':'Xmrig','pools':['Nanopool'],'version':'1'}]}
  self.b={'hardware':hw,'profile':'B','workload':[{'algorithms':['RandomX'],'devices':[{'name':'CPU'}],'miner':'Xmrig','pools':['Nanopool'],'version':'2'}]}
  self.bind=self.root/'binding.json'
  self.binding={'schema':BINDING_SCHEMA,'binding_id':'bind','node_id':'node','worker_id':'worker','hardware':hw,'adapter':'rainbowminer-json-v1','target':str(self.cfg),'watchdog_policy':{'max_temperature_c':75,'max_duration_seconds':2,'max_telemetry_age_seconds':5},'allowed_profiles':{'A':{'document':{'profile':'A'}},'B':{'document':{'profile':'B'}}}}
  self.write_binding(); self.make()
 def tearDown(self): self.td.cleanup()
 def write_binding(self): self.bind.write_text(json.dumps(self.binding),encoding='utf-8')
 def make(self,duration=0,min_samples=1):
  old=time.time
  try:
   time.time=self.clock.time
   self.pe=build_proposal('node',self.nk,self.bind,self.a,self.b,ttl=60,duration=duration,min_samples=min_samples,max_temp_c=75,max_telemetry_age=5)
   self.ie=make_intent('controller',self.ck,'node',self.pe,ttl=60)
  finally: time.time=old
 def telem(self,**kw):
  x={'temperature_c':60,'healthy':True,'sampled_at':self.clock.time()}; x.update(kw); return x
 def execute_case(self,reader=None,restore_fn=None,pe=None,ie=None):
  return execute('node',self.nk,self.nk.public_key(),'controller',self.ck.public_key(),pe or self.pe,ie or self.ie,self.bind,self.root/'runtime',self.root/'anti-replay.sqlite',reader or (lambda w:self.telem()),sleep=self.clock.sleep,clock=self.clock.time,monotonic=self.clock.monotonic,restore_fn=restore_fn)

 def test_success_restores_exact_baseline_and_never_apply(self):
  out=self.execute_case(); p=out['payload']; self.assertEqual(p['outcome'],'completed_restored'); self.assertTrue(p['baseline_restored']); self.assertFalse(p['production_apply']); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_replay_rejected_before_mutation(self):
  first=self.execute_case(); self.assertTrue(first['payload']['baseline_restored'])
  self.cfg.write_bytes(self.original)
  second=execute('node',self.nk,self.nk.public_key(),'controller',self.ck.public_key(),self.pe,self.ie,self.bind,self.root/'runtime2',self.root/'anti-replay.sqlite',lambda w:self.telem(),sleep=self.clock.sleep,clock=self.clock.time,monotonic=self.clock.monotonic)
  self.assertEqual(second['payload']['error'],'replay_detected'); self.assertFalse(second['payload']['baseline_restored']); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_tampered_proposal_signature_rejected(self):
  pe=copy.deepcopy(self.pe); pe['payload']['candidate_action']['to_profile']['profile']='A'
  out=self.execute_case(pe=pe); self.assertIn('invalid Ed25519',out['payload']['error']); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_tampered_intent_signature_rejected(self):
  ie=copy.deepcopy(self.ie); ie['payload']['production_apply']=True
  out=self.execute_case(ie=ie); self.assertIn('invalid Ed25519',out['payload']['error']); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_resigned_production_apply_is_denied(self):
  body=copy.deepcopy(self.ie['payload']); body['production_apply']=True
  ie=sign_envelope('mining-exploration-intent',INTENT_SCHEMA,'controller',self.ck,body)
  out=self.execute_case(ie=ie); self.assertEqual(out['payload']['error'],'production_apply_denied'); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_binding_changed_is_denied_before_mutation(self):
  self.binding['worker_id']='evil'; self.write_binding(); out=self.execute_case(); self.assertEqual(out['payload']['error'],'local_binding_changed'); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_thermal_trip_rolls_back(self):
  out=self.execute_case(lambda w:self.telem(temperature_c=76)); self.assertEqual(out['payload']['watchdog_trip'],'thermal'); self.assertEqual(out['payload']['outcome'],'aborted_restored'); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_health_trip_rolls_back(self):
  out=self.execute_case(lambda w:self.telem(healthy=False)); self.assertEqual(out['payload']['watchdog_trip'],'health'); self.assertTrue(out['payload']['baseline_restored']); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_staleness_trip_rolls_back(self):
  out=self.execute_case(lambda w:self.telem(sampled_at=self.clock.time()-6)); self.assertEqual(out['payload']['watchdog_trip'],'staleness'); self.assertTrue(out['payload']['baseline_restored']); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_deadline_trip_rolls_back(self):
  self.make(duration=1,min_samples=3)
  def reader(w): self.clock.sleep(0.6); return self.telem()
  out=self.execute_case(reader); self.assertEqual(out['payload']['watchdog_trip'],'deadline'); self.assertTrue(out['payload']['baseline_restored']); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_crash_in_telemetry_rolls_back(self):
  def crash(w): raise RuntimeError('telemetry_crash')
  out=self.execute_case(crash); self.assertEqual(out['payload']['outcome'],'aborted_restored'); self.assertIn('telemetry_crash',out['payload']['error']); self.assertEqual(self.cfg.read_bytes(),self.original)
 def test_rollback_failure_is_explicit_and_never_claims_restored(self):
  def fail(b,p): raise RollbackError('forced_rollback_failure')
  out=self.execute_case(lambda w:self.telem(temperature_c=90),restore_fn=fail); self.assertEqual(out['payload']['outcome'],'rollback_failed'); self.assertFalse(out['payload']['baseline_restored']); self.assertIn('forced_rollback_failure',out['payload']['error']); self.assertNotEqual(self.cfg.read_bytes(),self.original)
 def test_local_watchdog_caps_cannot_be_relaxed(self):
  old=time.time
  try:
   time.time=self.clock.time
   pe=build_proposal('node',self.nk,self.bind,self.a,self.b,duration=999,max_temp_c=999,max_telemetry_age=999)
  finally: time.time=old
  self.assertEqual(pe['payload']['watchdog']['max_temperature_c'],75); self.assertEqual(pe['payload']['watchdog']['duration_seconds'],2); self.assertEqual(pe['payload']['watchdog']['max_telemetry_age_seconds'],5)
 def test_algorithm_change_denied(self):
  bad=copy.deepcopy(self.b); bad['workload'][0]['algorithms']=['KawPOW']
  with self.assertRaisesRegex(ExplorationError,'algorithm_change_denied'): build_proposal('node',self.nk,self.bind,self.a,bad)
 def test_no_permanent_apply_api_or_true_literal(self):
  src=Path(__file__).parents[2]/'src/hashburst_node/exploration.py'; text=src.read_text(encoding='utf-8')
  self.assertNotIn('production_apply\':True',text.replace(' ',''))
  self.assertNotIn('hb-mining-apply-intent-v1',text)

if __name__=='__main__': unittest.main()
