import json,sqlite3,tempfile,unittest
from pathlib import Path
from hashburst_node.mining_adapter import telemetry_snapshot
class T(unittest.TestCase):
 def test_snapshot_is_aggregate_and_read_only(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td); (r/'accelerator.py').write_text('x'); (r/'policy.json').write_text('{}')
   db=sqlite3.connect(r/'history.sqlite'); db.executescript('CREATE TABLE samples(worker TEXT,sampled INTEGER,profile TEXT,payload TEXT,PRIMARY KEY(worker,sampled)); CREATE TABLE collections(collected INTEGER PRIMARY KEY,payload TEXT); CREATE TABLE worker_health(worker TEXT PRIMARY KEY,collected INTEGER,healthy INTEGER); CREATE TABLE local_identity(id INTEGER PRIMARY KEY,salt BLOB);')
   db.execute('INSERT INTO local_identity VALUES(1,?)',(b'x'*32,)); p={'temperature_c':70,'watts':100,'estimated_btc_day':.1,'accepted':2,'rejected_or_stale':1}; db.execute('INSERT INTO samples VALUES(?,?,?,?)',('secret-worker',1,'p',json.dumps(p))); db.commit(); db.close()
   before=(r/'history.sqlite').read_bytes(); o=telemetry_snapshot(r); self.assertEqual(o['workers_total'],1); self.assertNotIn('secret-worker',json.dumps(o)); self.assertEqual(before,(r/'history.sqlite').read_bytes())
if __name__=='__main__': unittest.main()
