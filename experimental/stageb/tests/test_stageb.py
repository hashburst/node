import json,tempfile,time,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from hashburst_node.exploration import *

class T(unittest.TestCase):
 def profiles(self):
  hw='h'*64
  a={'hardware':hw,'profile':'A','workload':[{'algorithms':['RandomX'],'devices':[{'id':'0','name':'Ryzen'}],'miner':'Xmrig','pools':['Nanopool'],'version':'1'}]}
  b={'hardware':hw,'profile':'B','workload':[{'algorithms':['RandomX'],'devices':[{'id':'0','name':'Ryzen'}],'miner':'SrbMinerMulti','pools':['Nanopool'],'version':'2'}]}
  return a,b
 def test_semantic_reject_algorithm_change(self):
  a,b=self.profiles(); b['workload'][0]['algorithms']=['KawPOW']
  with tempfile.TemporaryDirectory() as td:
   r=Path(td); bind=r/'b.json'; bind.write_text(json.dumps({'schema':BINDING_SCHEMA,'binding_id':'x','node_id':'n','worker_id':'w','hardware':'h'*64,'adapter':'rainbowminer-json-v1','target':str(r/'cfg.json'),'allowed_profiles':{'A':{},'B':{}}}))
   with self.assertRaises(ExplorationError): build_plan('n',Ed25519PrivateKey.generate(),bind,a,b)
 def test_signed_plan_intent_explore_and_restore(self):
  nk=Ed25519PrivateKey.generate(); ck=Ed25519PrivateKey.generate(); a,b=self.profiles()
  with tempfile.TemporaryDirectory() as td:
   r=Path(td); cfg=r/'cfg.json'; original=b'{"profile":"A"}\n'; cfg.write_bytes(original)
   bind=r/'binding.json'; bind.write_text(json.dumps({'schema':BINDING_SCHEMA,'binding_id':'bind1','node_id':'node','worker_id':'worker-hmac','hardware':'h'*64,'adapter':'rainbowminer-json-v1','target':str(cfg),'allowed_profiles':{'A':{'document':{'profile':'A'}},'B':{'document':{'profile':'B'}}}}))
   pe=build_plan('node',nk,bind,a,b,ttl=60,duration=0,min_samples=2,max_temp_c=80); ie=make_apply_intent('controller',ck,'node',pe,ttl=60)
   vals=iter([{'temperature_c':60,'healthy':True},{'temperature_c':61,'healthy':True}])
   out=execute_exploration('node',nk,nk.public_key(),'controller',ck.public_key(),pe,ie,bind,r/'runtime',lambda w:next(vals),sleep=lambda x:None)
   self.assertEqual(out['payload']['outcome'],'completed_restored'); self.assertEqual(cfg.read_bytes(),original); self.assertTrue(out['payload']['baseline_restored'])
 def test_thermal_trip_rolls_back(self):
  nk=Ed25519PrivateKey.generate(); ck=Ed25519PrivateKey.generate(); a,b=self.profiles()
  with tempfile.TemporaryDirectory() as td:
   r=Path(td); cfg=r/'cfg.json'; original=b'{"profile":"A"}\n'; cfg.write_bytes(original)
   bind=r/'binding.json'; bind.write_text(json.dumps({'schema':BINDING_SCHEMA,'binding_id':'bind1','node_id':'node','worker_id':'w','hardware':'h'*64,'adapter':'rainbowminer-json-v1','target':str(cfg),'allowed_profiles':{'A':{'document':{'profile':'A'}},'B':{'document':{'profile':'B'}}}}))
   pe=build_plan('node',nk,bind,a,b,ttl=60,duration=0,min_samples=1,max_temp_c=70); ie=make_apply_intent('controller',ck,'node',pe,ttl=60)
   out=execute_exploration('node',nk,nk.public_key(),'controller',ck.public_key(),pe,ie,bind,r/'runtime',lambda w:{'temperature_c':71,'healthy':True},sleep=lambda x:None)
   self.assertEqual(out['payload']['outcome'],'aborted_restored'); self.assertTrue(out['payload']['thermal_trip']); self.assertEqual(cfg.read_bytes(),original)
 def test_tampered_binding_fails(self):
  nk=Ed25519PrivateKey.generate(); a,b=self.profiles()
  with tempfile.TemporaryDirectory() as td:
   r=Path(td); cfg=r/'cfg.json'; cfg.write_text('{}'); bind=r/'binding.json'; obj={'schema':BINDING_SCHEMA,'binding_id':'x','node_id':'node','worker_id':'w','hardware':'h'*64,'adapter':'rainbowminer-json-v1','target':str(cfg),'allowed_profiles':{'A':{'document':{}},'B':{'document':{'x':1}}}}; bind.write_text(json.dumps(obj)); pe=build_plan('node',nk,bind,a,b); obj['worker_id']='other'; bind.write_text(json.dumps(obj)); self.assertNotEqual(pe['payload']['candidate_action']['binding_sha256'],sha_file(bind))
if __name__=='__main__': unittest.main()