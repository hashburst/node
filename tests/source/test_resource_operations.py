import ast
from pathlib import Path

import pytest

from hashburst_node.resource_operations import (
    ElasticWorkloadAdmission,
    ResourceOperationalSignal,
    RoutingPreference,
    operational_signal,
)
from hashburst_node.resource_readiness import (
    ResourceReadiness,
    ResourceReadinessState,
)


def test_ready_allows_elastic_work_and_is_preferred():
    signal = operational_signal(
        ResourceReadinessState(
            readiness=ResourceReadiness.READY
        )
    )

    assert signal.readiness is ResourceReadiness.READY
    assert (
        signal.elastic_workload
        is ElasticWorkloadAdmission.ALLOW
    )
    assert signal.routing is RoutingPreference.PREFERRED
    assert signal.schema == "hashburst-resource-operational-signal-v1"


def test_degraded_throttles_and_is_avoided_if_possible():
    signal = operational_signal(
        ResourceReadinessState(
            readiness=ResourceReadiness.DEGRADED
        )
    )

    assert signal.readiness is ResourceReadiness.DEGRADED
    assert (
        signal.elastic_workload
        is ElasticWorkloadAdmission.THROTTLE
    )
    assert (
        signal.routing
        is RoutingPreference.AVOID_IF_POSSIBLE
    )


def test_invalid_schema_fails_closed():
    with pytest.raises(
        ValueError,
        match="operational_signal_schema_invalid",
    ):
        ResourceOperationalSignal(
            schema="invalid",
            readiness=ResourceReadiness.READY,
            elastic_workload=ElasticWorkloadAdmission.ALLOW,
            routing=RoutingPreference.PREFERRED,
        )


def test_signal_has_no_consensus_authority_fields():
    fields = set(ResourceOperationalSignal.__dataclass_fields__)

    forbidden = {
        "validator",
        "validator_set",
        "validator_id",
        "quorum",
        "signature",
        "signing",
        "signing_eligibility",
        "voting_power",
        "vote",
        "finality",
        "consensus",
    }

    assert fields.isdisjoint(forbidden)

    assert fields == {
        "schema",
        "readiness",
        "elastic_workload",
        "routing",
    }


def test_operational_module_has_only_readiness_hashburst_dependency():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "hashburst_node"
        / "resource_operations.py"
    )

    tree = ast.parse(
        module_path.read_text(encoding="utf-8")
    )

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(
                alias.name for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    hashburst_imports = {
        name
        for name in imports
        if name.startswith("hashburst_node.")
    }

    assert hashburst_imports == {
        "hashburst_node.resource_readiness"
    }


def test_operational_module_has_no_executable_consensus_authority():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "hashburst_node"
        / "resource_operations.py"
    )

    tree = ast.parse(
        module_path.read_text(encoding="utf-8")
    )

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
