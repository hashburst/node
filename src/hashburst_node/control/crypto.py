from __future__ import annotations
import base64, getpass, json
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

class CryptoError(RuntimeError): pass

def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def load_public_doc(path: Path, expected_role: str) -> tuple[str, Ed25519PublicKey]:
    obj=json.loads(path.read_text(encoding="utf-8")); p=obj.get("payload",{})
    if obj.get("kind") != "public" or p.get("role") != expected_role or obj.get("algorithm") != "Ed25519":
        raise CryptoError(f"invalid {expected_role} public identity document")
    try: raw=bytes.fromhex(p["public_key"]); key=Ed25519PublicKey.from_public_bytes(raw)
    except Exception as e: raise CryptoError(f"invalid public key: {e}") from e
    return obj["key_id"], key

def _candidate_files(state: Path):
    preferred=["private-key.pem","private_key.pem","identity-private.pem","identity.pem","key.pem"]
    for n in preferred:
        p=state/n
        if p.is_file(): yield p
    for p in sorted(state.rglob("*")):
        if p.is_file() and p.suffix.lower() in {".pem",".key"} and p.name not in preferred: yield p

def load_matching_private(state: Path, public_doc: Path, role: str) -> tuple[str, Ed25519PrivateKey]:
    key_id, pub=load_public_doc(public_doc, role)
    expected=pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    candidates=list(dict.fromkeys(_candidate_files(state)))
    if not candidates:
        raise CryptoError("no PEM/KEY private-key candidate found in state; state was not modified")
    pw=getpass.getpass("Passphrase della chiave locale (minimo 16 caratteri): ").encode()
    errors=[]
    for p in candidates:
        try:
            k=serialization.load_pem_private_key(p.read_bytes(), password=pw)
            if not isinstance(k, Ed25519PrivateKey): continue
            raw=k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            if raw==expected: return key_id,k
        except Exception as e: errors.append(f"{p.name}: {type(e).__name__}")
    raise CryptoError("no private key in state matches supplied public identity ("+", ".join(errors[:5])+")")

def sign_envelope(kind: str, schema: str, signer_id: str, key: Ed25519PrivateKey, payload: dict) -> dict:
    body={"format":"hb-node-control-envelope-v1","algorithm":"Ed25519","kind":kind,"key_id":signer_id,"payload":payload}
    body["signature"]=key.sign(canonical(body)).hex(); return body

def verify_envelope(obj: dict, kind: str, pub: Ed25519PublicKey, key_id: str) -> dict:
    if obj.get("format")!="hb-node-control-envelope-v1" or obj.get("algorithm")!="Ed25519" or obj.get("kind")!=kind or obj.get("key_id")!=key_id:
        raise CryptoError("control envelope metadata mismatch")
    sig=obj.get("signature"); unsigned=dict(obj); unsigned.pop("signature",None)
    try: pub.verify(bytes.fromhex(sig), canonical(unsigned))
    except Exception as e: raise CryptoError("invalid Ed25519 control signature") from e
    return obj.get("payload",{})