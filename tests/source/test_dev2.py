import json,tempfile,time,unittest
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from hashburst_node.control.protocol import make_intent,process_intent,verify_result

def fixture(root,role,password=b"0123456789abcdef"):
    state=root/(role+"-state"); state.mkdir(); k=Ed25519PrivateKey.generate(); raw=k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    kid=(role[0]*64); pub=root/(role+"-public.json"); pub.write_text(json.dumps({"algorithm":"Ed25519","kind":"public","key_id":kid,"payload":{"role":role,"public_key":raw.hex()}}))
    pem=k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.BestAvailableEncryption(password)); (state/'private-key.pem').write_bytes(pem); return state,pub
class T(unittest.TestCase):
 def test_protocol_and_replay(self):
  import unittest.mock as m
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); cs,cp=fixture(r,'controller'); ns,np=fixture(r,'node'); intent=r/'i.json'; ack=r/'a.json'; nack=r/'n.json'; journal=r/'j.sqlite'
   with m.patch('getpass.getpass',return_value='0123456789abcdef'):
    make_intent(cs,cp,np,intent,ttl=60); a=process_intent(ns,np,cp,intent,journal,ack); self.assertEqual(a['payload']['result'],'ACK'); self.assertEqual(verify_result(cp,np,ack)['result'],'ACK'); n=process_intent(ns,np,cp,intent,journal,nack); self.assertEqual(n['payload']['result'],'NACK'); self.assertEqual(n['payload']['reason'],'replay_detected')
if __name__=='__main__': unittest.main()
