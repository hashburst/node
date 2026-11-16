import ast
from pathlib import Path

import pytest

from hashburst_node.resource_readiness import (
    ResourceObservation,
    ResourceReadiness,
    ResourceReadinessPolicy,
    ResourceReadinessState,
    evaluate_observations,
    evaluate_resource_readiness,
)


def observation(value: float, observed_at: float = 1.0):
    return ResourceObservation(
        observed_at=observed_at,
        cpu_utilization=value,
        memory_utilization=0.10,
        io_utilization=0.10,
        network_utilization=0.10,
        backlog_utilization=0.10,
    )


def policy():
    return ResourceReadinessPolicy(
        degrade_threshold=0.90,
        recover_threshold=0.75,
        degrade_observations=3,
        recover_observations=3,
    )


def test_transient_pressure_does_not_degrade():
    state = ResourceReadinessState()

    state = evaluate_resource_readiness(
        state, observation(0.95, 1), policy()
    )

    assert state.readiness is ResourceReadiness.READY
    assert state.consecutive_pressure == 1

    state = evaluate_resource_readiness(
        state, observation(0.20, 2), policy()
    )

    assert state.readiness is ResourceReadiness.READY
    assert state.consecutive_pressure == 0


def test_sustained_pressure_degrades_after_hysteresis():
    state = evaluate_observations(
        [
            observation(0.95, 1),
            observation(0.95, 2),
            observation(0.95, 3),
        ],
        policy(),
    )

    assert state.readiness is ResourceReadiness.DEGRADED


def test_degraded_state_does_not_recover_early():
    state = ResourceReadinessState(
        readiness=ResourceReadiness.DEGRADED
    )

    state = evaluate_resource_readiness(
        state, observation(0.50, 1), policy()
    )
    state = evaluate_resource_readiness(
        state, observation(0.50, 2), policy()
    )

    assert state.readiness is ResourceReadiness.DEGRADED
    assert state.consecutive_recovery == 2


def test_sustained_recovery_returns_ready():
    initial = ResourceReadinessState(
        readiness=ResourceReadiness.DEGRADED
    )

    state = evaluate_observations(
        [
            observation(0.50, 1),
            observation(0.50, 2),
            observation(0.50, 3),
        ],
        policy(),
        initial=initial,
    )

    assert state.readiness is ResourceReadiness.READY


def test_hysteresis_band_preserves_degraded_state():
    state = ResourceReadinessState(
        readiness=ResourceReadiness.DEGRADED
    )

    state = evaluate_resource_readiness(
        state, observation(0.82, 1), policy()
    )

    assert state.readiness is ResourceReadiness.DEGRADED
    assert state.consecutive_recovery == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("cpu_utilization", -0.01),
        ("cpu_utilization", 1.01),
        ("memory_utilization", float("nan")),
        ("io_utilization", float("inf")),
        ("network_utilization", -1.0),
        ("backlog_utilization", 2.0),
    ],
)
def test_invalid_observations_fail_closed(field, value):
    values = dict(
        observed_at=1.0,
        cpu_utilization=0.10,
        memory_utilization=0.10,
        io_utilization=0.10,
        network_utilization=0.10,
        backlog_utilization=0.10,
    )
    values[field] = value

    with pytest.raises(ValueError):
        ResourceObservation(**values)


def test_invalid_policy_rejects_missing_hysteresis():
    with pytest.raises(ValueError):
        ResourceReadinessPolicy(
            degrade_threshold=0.75,
            recover_threshold=0.75,
        )


def test_peak_resource_can_trigger_pressure():
    obs = ResourceObservation(
        observed_at=1.0,
        cpu_utilization=0.10,
        memory_utilization=0.10,
        io_utilization=0.95,
        network_utilization=0.10,
        backlog_utilization=0.10,
    )

    state = evaluate_resource_readiness(
        ResourceReadinessState(),
        obs,
        ResourceReadinessPolicy(degrade_observations=1),
    )

    assert state.readiness is ResourceReadiness.DEGRADED


def test_resource_module_has_no_mining_or_blockchain_imports():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "hashburst_node"
        / "resource_readiness.py"
    )

    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    forbidden = (
        "hashburst_node.mining_adapter",
        "hashburst_node.planning",
        "hashburst_node.exploration",
        "mining_adapter",
        "planning",
        "exploration",
        "blockchain",
    )

    assert not [
        name
        for name in imports
        if any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in forbidden
        )
    ]


def test_resource_module_has_no_consensus_authority_symbols():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "hashburst_node"
        / "resource_readiness.py"
    )

    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    forbidden = {
        "validator_set",
        "validatorset",
        "active_set",
        "activeset",
        "quorum",
        "voting_power",
        "signing_eligibility",
        "finality",
    }

    executable_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            executable_names.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            executable_names.add(node.attr.lower())
        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            executable_names.add(node.name.lower())

    assert executable_names.isdisjoint(forbidden)
