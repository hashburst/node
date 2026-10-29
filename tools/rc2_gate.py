#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((root/'release/manifest-v0.1.0-rc2.json').read_text())
errors=[]
def need(ok,msg):
 if not ok: errors.append(msg)
need(m.get('release')=='v0.1.0-rc2','release mismatch')
need(m.get('base_tag')=='v0.1.0-rc1','RC1 base mismatch')
need(m.get('mainnet') is False,'mainnet must be false')
need(m.get('production_apply') is False,'production_apply must be false')
f=m.get('features',{})
for k in ('signed_controlled_exploration','persistent_anti_replay_required','watchdog_required','rollback_required','baseline_restore_required'):
 need(f.get(k) is True,k+' must be true')
need(f.get('permanent_apply') is False,'permanent_apply must be false')
s=m.get('security_invariants',{})
need(s.get('arbitrary_shell') is False,'arbitrary shell forbidden')
need(s.get('controller_supplied_executable_paths') is False,'controller executable paths forbidden')
need(s.get('controller_supplied_arbitrary_urls') is False,'controller URLs forbidden')
need(s.get('one_worker_canary') is True,'one-worker canary required')
src=(root/'src/hashburst_node/exploration.py').read_text(encoding='utf-8').replace(' ','')
need("'production_apply':True" not in src,'runtime contains production_apply=True')
need('hb-mining-apply-intent-v1' not in src,'permanent APPLY schema present')
if errors:
 print('\n'.join('FAIL: '+x for x in errors)); sys.exit(1)
print('PASS: RC2 static release gate')
