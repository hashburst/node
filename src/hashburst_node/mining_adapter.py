from __future__ import annotations
import hashlib, json, os, sqlite3, subprocess, sys, tempfile
from contextlib import closing
from pathlib import Path

class MiningError(RuntimeError): pass
CRITICAL=("accelerator.py","policy.json","history.sqlite")

def sha(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def baseline(root:Path):
    root=root.resolve(strict=True)
    if not root.is_dir(): raise MiningError('accelerator_root_invalid')
    files={}
    for name in CRITICAL:
        p=root/name
        if not p.is_file(): raise MiningError('accelerator_baseline_incomplete')
        files[name]=sha(p)
    return root,files

def unchanged(root:Path,before:dict):
    after={n:sha(root/n) for n in before}
    if after!=before: raise MiningError('accelerator_baseline_modified')
    return after

def run_json(root:Path,args:list[str]):
    cmd=[sys.executable,'-B',str(root/'accelerator.py')]+args
    cp=subprocess.run(cmd,cwd=str(root),capture_output=True,text=True,timeout=60,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if cp.returncode: raise MiningError('accelerator_command_failed')
    try: return json.loads(cp.stdout)
    except Exception as e: raise MiningError('accelerator_output_invalid') from e

def capabilities(root:Path):
    root,b=baseline(root); out=run_json(root,['doctor']); unchanged(root,b)
    if out.get('version')!='0.1.2' or out.get('accelerator_mode')!='shadow' or out.get('apply_supported') is not False: raise MiningError('accelerator_safety_contract_mismatch')
    return {'schema':'hb-node-mining-capabilities-v1','accelerator_version':'0.1.2','mode':'shadow','read_only_bridge':True,'apply_supported':False,'doctor':out}

def status(root:Path):
    root,b=baseline(root); out=run_json(root,['status','--db',str(root/'history.sqlite'),'--policy',str(root/'policy.json')]); unchanged(root,b)
    if out.get('version')!='0.1.2' or out.get('read_only') is not True or out.get('mode')!='shadow' or out.get('apply_supported') is not False: raise MiningError('accelerator_safety_contract_mismatch')
    return out

def telemetry_snapshot(root:Path):
    root,b=baseline(root); dbp=root/'history.sqlite'
    uri=dbp.as_uri()+'?mode=ro&immutable=1'
    with closing(sqlite3.connect(uri,uri=True,timeout=5)) as db:
        db.execute('PRAGMA query_only=ON'); db.execute('PRAGMA trusted_schema=OFF')
        if db.execute('PRAGMA quick_check').fetchall()!=[('ok',)]: raise MiningError('history_integrity_failed')
        total,workers,oldest,newest=db.execute('SELECT count(*),count(DISTINCT worker),min(sampled),max(sampled) FROM samples').fetchone()
        collections,last=db.execute('SELECT count(*),max(collected) FROM collections').fetchone()
        last_counts=None
        if last is not None:
            row=db.execute('SELECT payload FROM collections WHERE collected=?',(last,)).fetchone()
            if row: last_counts=json.loads(row[0]).get('workers')
        # Aggregate latest sample per worker; never export worker identifiers/workload details.
        rows=db.execute('SELECT s.payload FROM samples s JOIN (SELECT worker,max(sampled) m FROM samples GROUP BY worker) x ON s.worker=x.worker AND s.sampled=x.m').fetchall()
        temps=[]; watts=[]; btc=[]; accepted=0; rejected=0
        for (raw,) in rows:
            v=json.loads(raw); 
            if isinstance(v.get('temperature_c'),(int,float)): temps.append(v['temperature_c'])
            if isinstance(v.get('watts'),(int,float)): watts.append(v['watts'])
            if isinstance(v.get('estimated_btc_day'),(int,float)): btc.append(v['estimated_btc_day'])
            accepted += v.get('accepted',0) if isinstance(v.get('accepted',0),(int,float)) else 0
            rejected += v.get('rejected_or_stale',0) if isinstance(v.get('rejected_or_stale',0),(int,float)) else 0
    unchanged(root,b)
    return {'schema':'hb-node-mining-telemetry-snapshot-v1','source':'accelerator-history-0.1.2','read_only':True,'network_calls':0,'samples_total':total,'workers_total':workers,'oldest_sample_at':oldest,'newest_sample_at':newest,'collections_total':collections,'last_collection_at':last,'last_collection_counts':last_counts,'latest_workers_observed':len(rows),'temperature_c_max':max(temps) if temps else None,'power_w_total_latest':sum(watts) if watts else None,'estimated_btc_day_total_latest':sum(btc) if btc else None,'accepted_total_latest':accepted,'rejected_or_stale_total_latest':rejected}

def shadow(root:Path,runtime_dir:Path):
    root,b=baseline(root); runtime_dir.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='shadow-',suffix='.json',dir=str(runtime_dir)); os.close(fd); os.unlink(tmp)
    outp=Path(tmp)
    cmd=[sys.executable,'-B',str(root/'accelerator.py'),'recommend','--db',str(root/'history.sqlite'),'--policy',str(root/'policy.json'),'--out',str(outp)]
    cp=subprocess.run(cmd,cwd=str(root),capture_output=True,text=True,timeout=60,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if cp.returncode or not outp.is_file(): raise MiningError('accelerator_shadow_failed')
    out=json.loads(outp.read_text(encoding='utf-8')); digest=sha(outp); unchanged(root,b)
    if out.get('mode')!='shadow' or out.get('apply_supported') is not False: raise MiningError('accelerator_safety_contract_mismatch')
    counts={}
    for d in out.get('decisions',[]): counts[d.get('action','unknown')]=counts.get(d.get('action','unknown'),0)+1
    return {'schema':'hb-node-mining-shadow-result-v1','mode':'shadow','apply_supported':False,'proposal_sha256':digest,'proposal_file':str(outp),'decision_counts':counts,'decisions_total':len(out.get('decisions',[]))}