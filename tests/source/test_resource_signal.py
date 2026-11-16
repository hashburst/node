import copy

import pytest

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from hashburst_node.control.crypto import CryptoError
from hashburst_node.resource_operations import operational_signal
from hashburst_node.resource_readiness import (
    ResourceReadiness,
    ResourceReadinessState,
)
from hashburst_node.resource_signal import (
    build_signed_resource_signal,
    verify_resource_signal,
)


NODE_ID = "a" * 64
NOW = 2_000_000_000


def state(readiness):
    return ResourceReadinessState(readiness=readiness)


def signed(readiness=ResourceReadiness.READY, ttl=30):
    key = Ed25519PrivateKey.generate()

    envelope = build_signed_resource_signal(
        operational_signal(state(readiness)),
        NODE_ID,
        key,
        signal_id="signal-001",
        observed_at=NOW,
        ttl=ttl,
    )

    return key, envelope


def test_ready_signal_signs_and_verifies():
    key, envelope = signed()

    payload = verify_resource_signal(
        envelope,
        key.public_key(),
        NODE_ID,
        now=NOW,
    )

    assert payload["readiness"] == "READY"
    assert payload["elastic_workload"] == "ALLOW"
    assert payload["routing"] == "PREFERRED"


def test_degraded_signal_signs_and_verifies():
    key, envelope = signed(ResourceReadiness.DEGRADED)

    payload = verify_resource_signal(
        envelope,
        key.public_key(),
        NODE_ID,
        now=NOW,
    )

    assert payload["readiness"] == "DEGRADED"
    assert payload["elastic_workload"] == "THROTTLE"
    assert payload["routing"] == "AVOID_IF_POSSIBLE"


def test_payload_tampering_is_rejected():
    key, envelope = signed()

    tampered = copy.deepcopy(envelope)
    tampered["payload"]["routing"] = "AVOID_IF_POSSIBLE"

    with pytest.raises(
        CryptoError,
        match="invalid Ed25519 resource signal signature",
    ):
        verify_resource_signal(
            tampered,
            key.public_key(),
            NODE_ID,
            now=NOW,
        )


def test_signature_tampering_is_rejected():
    key, envelope = signed()

    tampered = copy.deepcopy(envelope)
    tampered["signature"] = "00" * 64

    with pytest.raises(
        CryptoError,
        match="invalid Ed25519 resource signal signature",
    ):
        verify_resource_signal(
            tampered,
            key.public_key(),
            NODE_ID,
            now=NOW,
        )


def test_wrong_public_key_is_rejected():
    _, envelope = signed()
    other = Ed25519PrivateKey.generate()

    with pytest.raises(
        CryptoError,
        match="invalid Ed25519 resource signal signature",
    ):
        verify_resource_signal(
            envelope,
            other.public_key(),
            NODE_ID,
            now=NOW,
        )


def test_wrong_expected_node_is_rejected():
    key, envelope = signed()

    with pytest.raises(
        CryptoError,
        match="resource_signal_key_binding_invalid",
    ):
        verify_resource_signal(
            envelope,
            key.public_key(),
            "b" * 64,
            now=NOW,
        )


def test_expired_signal_is_rejected():
    key, envelope = signed(ttl=10)

    with pytest.raises(
        CryptoError,
        match="resource_signal_expired",
    ):
        verify_resource_signal(
            envelope,
            key.public_key(),
            NODE_ID,
            now=NOW + 11,
        )


def test_future_signal_outside_skew_is_rejected():
    key, envelope = signed()

    with pytest.raises(
        CryptoError,
        match="resource_signal_not_yet_valid",
    ):
        verify_resource_signal(
            envelope,
            key.public_key(),
            NODE_ID,
            now=NOW - 31,
        )


def test_ttl_is_bounded():
    key = Ed25519PrivateKey.generate()

    with pytest.raises(
        CryptoError,
        match="resource_signal_ttl_invalid",
    ):
        build_signed_resource_signal(
            operational_signal(
                state(ResourceReadiness.READY)
            ),
            NODE_ID,
            key,
            signal_id="signal-ttl",
            observed_at=NOW,
            ttl=301,
        )


def test_signal_has_no_consensus_authority_payload():
    key, envelope = signed(ResourceReadiness.DEGRADED)

    forbidden = {
        "validator",
        "validator_set",
        "validator_id",
        "active_set",
        "quorum",
        "vote",
        "voting_power",
        "signature_eligibility",
        "signing_eligibility",
        "finality",
        "consensus",
    }

    assert set(envelope["payload"]).isdisjoint(forbidden)


def test_existing_control_envelope_is_not_reused():
    _, envelope = signed()

    assert (
        envelope["format"]
        == "hb-node-resource-signal-envelope-v1"
    )
    assert envelope["kind"] == "resource-operational-signal"
    assert envelope["format"] != "hb-node-control-envelope-v1"
