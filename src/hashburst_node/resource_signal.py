from __future__ import annotations

from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from hashburst_node.control.crypto import CryptoError, canonical
from hashburst_node.resource_operations import (
    ResourceOperationalSignal,
)


FORMAT = "hb-node-resource-signal-envelope-v1"
KIND = "resource-operational-signal"
SCHEMA = "hashburst-resource-operational-signal-v1"
PROVENANCE = "hashburst-node-resource-readiness-v1"

MAX_TTL_SECONDS = 300
MAX_FUTURE_SKEW_SECONDS = 30


def _validate_payload(payload: dict[str, Any]) -> None:
    required = {
        "schema",
        "signal_id",
        "node_id",
        "observed_at",
        "expires_at",
        "readiness",
        "elastic_workload",
        "routing",
        "provenance",
    }

    if set(payload) != required:
        raise CryptoError("resource_signal_payload_shape_invalid")

    if payload.get("schema") != SCHEMA:
        raise CryptoError("resource_signal_schema_invalid")

    if not isinstance(payload.get("signal_id"), str) or not payload["signal_id"]:
        raise CryptoError("resource_signal_id_invalid")

    if not isinstance(payload.get("node_id"), str) or not payload["node_id"]:
        raise CryptoError("resource_signal_node_id_invalid")

    observed_at = payload.get("observed_at")
    expires_at = payload.get("expires_at")

    if not isinstance(observed_at, int) or not isinstance(expires_at, int):
        raise CryptoError("resource_signal_time_invalid")

    ttl = expires_at - observed_at

    if ttl < 1 or ttl > MAX_TTL_SECONDS:
        raise CryptoError("resource_signal_ttl_invalid")

    if payload.get("readiness") not in {"READY", "DEGRADED"}:
        raise CryptoError("resource_signal_readiness_invalid")

    if payload.get("elastic_workload") not in {"ALLOW", "THROTTLE"}:
        raise CryptoError("resource_signal_workload_invalid")

    if payload.get("routing") not in {
        "PREFERRED",
        "AVOID_IF_POSSIBLE",
    }:
        raise CryptoError("resource_signal_routing_invalid")

    if payload.get("provenance") != PROVENANCE:
        raise CryptoError("resource_signal_provenance_invalid")

    if payload["readiness"] == "READY":
        if payload["elastic_workload"] != "ALLOW":
            raise CryptoError("resource_signal_policy_mismatch")
        if payload["routing"] != "PREFERRED":
            raise CryptoError("resource_signal_policy_mismatch")

    if payload["readiness"] == "DEGRADED":
        if payload["elastic_workload"] != "THROTTLE":
            raise CryptoError("resource_signal_policy_mismatch")
        if payload["routing"] != "AVOID_IF_POSSIBLE":
            raise CryptoError("resource_signal_policy_mismatch")


def build_signed_resource_signal(
    operational: ResourceOperationalSignal,
    node_id: str,
    private_key: Ed25519PrivateKey,
    *,
    signal_id: str,
    observed_at: int,
    ttl: int = 30,
) -> dict[str, Any]:
    if not isinstance(node_id, str) or not node_id:
        raise CryptoError("resource_signal_node_id_invalid")

    if not isinstance(signal_id, str) or not signal_id:
        raise CryptoError("resource_signal_id_invalid")

    if not isinstance(observed_at, int):
        raise CryptoError("resource_signal_time_invalid")

    if not isinstance(ttl, int) or ttl < 1 or ttl > MAX_TTL_SECONDS:
        raise CryptoError("resource_signal_ttl_invalid")

    payload = {
        "schema": SCHEMA,
        "signal_id": signal_id,
        "node_id": node_id,
        "observed_at": observed_at,
        "expires_at": observed_at + ttl,
        "readiness": operational.readiness.value,
        "elastic_workload": operational.elastic_workload.value,
        "routing": operational.routing.value,
        "provenance": PROVENANCE,
    }

    _validate_payload(payload)

    envelope = {
        "format": FORMAT,
        "algorithm": "Ed25519",
        "kind": KIND,
        "key_id": node_id,
        "payload": payload,
    }

    envelope["signature"] = private_key.sign(
        canonical(envelope)
    ).hex()

    return envelope


def verify_resource_signal(
    envelope: dict[str, Any],
    public_key: Ed25519PublicKey,
    expected_node_id: str,
    *,
    now: int,
) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise CryptoError("resource_signal_envelope_invalid")

    signature = envelope.get("signature")

    if not isinstance(signature, str) or not signature:
        raise CryptoError("resource_signal_signature_missing")

    unsigned = dict(envelope)
    unsigned.pop("signature", None)

    try:
        signature_bytes = bytes.fromhex(signature)
        public_key.verify(
            signature_bytes,
            canonical(unsigned),
        )
    except Exception as exc:
        raise CryptoError(
            "invalid Ed25519 resource signal signature"
        ) from exc

    if envelope.get("format") != FORMAT:
        raise CryptoError("resource_signal_format_invalid")

    if envelope.get("algorithm") != "Ed25519":
        raise CryptoError("resource_signal_algorithm_invalid")

    if envelope.get("kind") != KIND:
        raise CryptoError("resource_signal_kind_invalid")

    if envelope.get("key_id") != expected_node_id:
        raise CryptoError("resource_signal_key_binding_invalid")

    payload = envelope.get("payload")

    if not isinstance(payload, dict):
        raise CryptoError("resource_signal_payload_invalid")

    _validate_payload(payload)

    if payload.get("node_id") != expected_node_id:
        raise CryptoError("resource_signal_node_binding_invalid")

    if not isinstance(now, int):
        raise CryptoError("resource_signal_now_invalid")

    if payload["observed_at"] > now + MAX_FUTURE_SKEW_SECONDS:
        raise CryptoError("resource_signal_not_yet_valid")

    if payload["expires_at"] < now:
        raise CryptoError("resource_signal_expired")

    return payload
