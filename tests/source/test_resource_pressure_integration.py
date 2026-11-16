import copy

import pytest

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from hashburst_node.control.crypto import CryptoError
from hashburst_node.resource_operations import (
    ElasticWorkloadAdmission,
    RoutingPreference,
    operational_signal,
)
from hashburst_node.resource_readiness import (
    ResourceObservation,
    ResourceReadiness,
    ResourceReadinessPolicy,
    ResourceReadinessState,
    evaluate_resource_readiness,
)
from hashburst_node.resource_signal import (
    build_signed_resource_signal,
    verify_resource_signal,
)


NODE_ID = "c" * 64
NOW = 2_100_000_000


def observation(value, at):
    return ResourceObservation(
        observed_at=at,
        cpu_utilization=value,
        memory_utilization=value,
        io_utilization=value,
        network_utilization=value,
        backlog_utilization=value,
        provenance="host-resource-observation-v1",
    )


def initial_state():
    return ResourceReadinessState(
        readiness=ResourceReadiness.READY
    )


def evaluate_sequence(values):
    policy = ResourceReadinessPolicy(
        degrade_threshold=0.90,
        recover_threshold=0.75,
        degrade_observations=3,
        recover_observations=3,
    )

    state = initial_state()
    states = []

    for index, value in enumerate(values):
        state = evaluate_resource_readiness(
            state,
            observation(value, NOW + index),
            policy,
        )
        states.append(state)

    return states


def signed_from_state(state, key, suffix, observed_at):
    operational = operational_signal(state)

    envelope = build_signed_resource_signal(
        operational,
        NODE_ID,
        key,
        signal_id="pressure-" + suffix,
        observed_at=observed_at,
        ttl=30,
    )

    return operational, envelope


def test_transient_pressure_does_not_degrade():
    states = evaluate_sequence([
        0.20,
        0.95,
        0.20,
    ])

    assert all(
        state.readiness is ResourceReadiness.READY
        for state in states
    )


def test_sustained_pressure_degrades_only_after_hysteresis():
    states = evaluate_sequence([
        0.20,
        0.95,
        0.95,
        0.95,
    ])

    assert states[0].readiness is ResourceReadiness.READY
    assert states[1].readiness is ResourceReadiness.READY
    assert states[2].readiness is ResourceReadiness.READY
    assert states[3].readiness is ResourceReadiness.DEGRADED


def test_degraded_state_produces_signed_throttle_and_avoid():
    states = evaluate_sequence([
        0.95,
        0.95,
        0.95,
    ])

    degraded = states[-1]
    assert degraded.readiness is ResourceReadiness.DEGRADED

    key = Ed25519PrivateKey.generate()

    operational, envelope = signed_from_state(
        degraded,
        key,
        "degraded",
        NOW + 2,
    )

    assert (
        operational.elastic_workload
        is ElasticWorkloadAdmission.THROTTLE
    )
    assert (
        operational.routing
        is RoutingPreference.AVOID_IF_POSSIBLE
    )

    payload = verify_resource_signal(
        envelope,
        key.public_key(),
        NODE_ID,
        now=NOW + 2,
    )

    assert payload["readiness"] == "DEGRADED"
    assert payload["elastic_workload"] == "THROTTLE"
    assert payload["routing"] == "AVOID_IF_POSSIBLE"


def test_recovery_requires_full_hysteresis():
    states = evaluate_sequence([
        0.95,
        0.95,
        0.95,
        0.20,
        0.20,
        0.20,
    ])

    assert states[2].readiness is ResourceReadiness.DEGRADED
    assert states[3].readiness is ResourceReadiness.DEGRADED
    assert states[4].readiness is ResourceReadiness.DEGRADED
    assert states[5].readiness is ResourceReadiness.READY


def test_recovered_state_produces_signed_allow_and_preferred():
    states = evaluate_sequence([
        0.95,
        0.95,
        0.95,
        0.20,
        0.20,
        0.20,
    ])

    recovered = states[-1]

    key = Ed25519PrivateKey.generate()

    operational, envelope = signed_from_state(
        recovered,
        key,
        "recovered",
        NOW + 5,
    )

    assert (
        operational.elastic_workload
        is ElasticWorkloadAdmission.ALLOW
    )
    assert operational.routing is RoutingPreference.PREFERRED

    payload = verify_resource_signal(
        envelope,
        key.public_key(),
        NODE_ID,
        now=NOW + 5,
    )

    assert payload["readiness"] == "READY"
    assert payload["elastic_workload"] == "ALLOW"
    assert payload["routing"] == "PREFERRED"


def test_tampered_pressure_signal_is_rejected():
    states = evaluate_sequence([
        0.95,
        0.95,
        0.95,
    ])

    key = Ed25519PrivateKey.generate()

    _, envelope = signed_from_state(
        states[-1],
        key,
        "tamper",
        NOW + 2,
    )

    tampered = copy.deepcopy(envelope)
    tampered["payload"]["readiness"] = "READY"

    with pytest.raises(
        CryptoError,
        match="invalid Ed25519 resource signal signature",
    ):
        verify_resource_signal(
            tampered,
            key.public_key(),
            NODE_ID,
            now=NOW + 2,
        )


def test_stale_pressure_signal_is_rejected():
    states = evaluate_sequence([
        0.95,
        0.95,
        0.95,
    ])

    key = Ed25519PrivateKey.generate()

    _, envelope = signed_from_state(
        states[-1],
        key,
        "stale",
        NOW + 2,
    )

    with pytest.raises(
        CryptoError,
        match="resource_signal_expired",
    ):
        verify_resource_signal(
            envelope,
            key.public_key(),
            NODE_ID,
            now=NOW + 33,
        )


def test_pressure_signal_contains_no_consensus_authority():
    states = evaluate_sequence([
        0.95,
        0.95,
        0.95,
    ])

    key = Ed25519PrivateKey.generate()

    _, envelope = signed_from_state(
        states[-1],
        key,
        "boundary",
        NOW + 2,
    )

    forbidden = {
        "validator",
        "validator_set",
        "validator_id",
        "active_set",
        "quorum",
        "vote",
        "voting_power",
        "signing",
        "signing_eligibility",
        "finality",
        "consensus",
    }

    assert set(envelope["payload"]).isdisjoint(forbidden)
