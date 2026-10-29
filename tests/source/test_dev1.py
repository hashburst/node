import json, os, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from hashburst_node.paths import resolve_state_path
from hashburst_node.status import build_status

NODE_ID="d652939c020cb91df5b2f4a78265e8d76a61c99d39fae733f2ef172dc8214f83"
class Tests(unittest.TestCase):
  def test_cli_precedence(self):
    with patch.dict(os.environ,{"HB_NODE_STATE_PATH":"/env"}): self.assertEqual(str(resolve_state_path("/cli","/cfg")[0]),"/cli")
  def test_env_precedence(self):
    with patch.dict(os.environ,{"HB_NODE_STATE_PATH":"/env"}): self.assertEqual(str(resolve_state_path(None,"/cfg")[0]),"/env")
  def test_config_precedence(self):
    with patch.dict(os.environ,{},clear=True): self.assertEqual(str(resolve_state_path(None,"/cfg")[0]),"/cfg")
  def test_status_is_read_only_and_disabled(self):
    with tempfile.TemporaryDirectory() as td:
      d=Path(td); state=d/'state'; state.mkdir()
      pub=d/'pub.json'; pub.write_text(json.dumps({"kind":"public","key_id":NODE_ID,"algorithm":"Ed25519","payload":{"role":"node","scope":"enrollment-read-only","schema":"hb-node-public-v1"}}))
      con=d/'confirm.json'; con.write_text(json.dumps({"schema":"hb-enrollment-confirmation-v1","identity_registry_confirmed":True,"binding_assurance":"not_bound","worker_binding_present":False}))
      a=SimpleNamespace(state_path=str(state),config_state_path=None,node_public=str(pub),enrollment_confirmation=str(con),enrollment_cli=None,enrollment_python=None)
      s=build_status(a); self.assertEqual(s['node_id'],NODE_ID); self.assertTrue(s['identity']['enrollment_confirmed']); self.assertFalse(s['control_plane']['production_apply']); self.assertEqual(s['safety']['network_calls'],0)
if __name__=='__main__': unittest.main()