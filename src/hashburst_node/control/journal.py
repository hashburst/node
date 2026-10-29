from __future__ import annotations
import sqlite3, time
from pathlib import Path
class ReplayError(RuntimeError): pass

def consume(db: Path, intent_id: str, intent_sha256: str):
    db.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(db)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS consumed_intents(intent_id TEXT PRIMARY KEY,intent_sha256 TEXT NOT NULL,consumed_at INTEGER NOT NULL)")
        try:
            con.execute("INSERT INTO consumed_intents VALUES(?,?,?)",(intent_id,intent_sha256,int(time.time())))
            con.commit()
        except sqlite3.IntegrityError as e: raise ReplayError("replay_detected") from e
    finally: con.close()