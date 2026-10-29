from __future__ import annotations
import sqlite3,time
from pathlib import Path

def record(db:Path,intent_id:str,state:str,detail:str=''):
 db.parent.mkdir(parents=True,exist_ok=True); con=sqlite3.connect(db)
 try:
  con.execute('CREATE TABLE IF NOT EXISTS intent_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,intent_id TEXT NOT NULL,state TEXT NOT NULL,detail TEXT NOT NULL,event_at INTEGER NOT NULL)')
  con.execute('INSERT INTO intent_events(intent_id,state,detail,event_at) VALUES(?,?,?,?)',(intent_id,state,detail,int(time.time()))); con.commit()
 finally: con.close()
