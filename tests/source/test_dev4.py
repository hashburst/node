import json,tempfile,unittest,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from hashburst_node.control.crypto import sign_envelope
from hashburst_node.planning import verify_proposal
class T(unittest.TestCase):
 def test_signed_proposal_verification_and_apply_false(self):
  k=Ed25519PrivateKey.generate(); pub=k.public_key(); nid='n'*64; now=int(time.time())
  p={'schema':'hb-mining-proposal-v1','proposal_id':'x','node_id':nid,'created_at':now,'expires_at':now+60,'mode':'shadow','production_apply':False,'apply_supported':False,'decision':'blocked','block_reasons':['freshness'],'gates':{},'shadow':{},'provenance':{}}
  e=sign_envelope('mining-proposal','hb-mining-proposal-v1',nid,k,p)
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'p.json'; f.write_text(json.dumps(e))
   q=verify_proposal(pub,nid,f,now); self.assertFalse(q['production_apply']); self.assertEqual(q['decision'],'blocked')
