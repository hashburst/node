from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hashburst_node.resource_readiness import (
    ResourceReadiness,
    ResourceReadinessState,
)


class ElasticWorkloadAdmission(str, Enum):
    ALLOW = "ALLOW"
    THROTTLE = "THROTTLE"


class RoutingPreference(str, Enum):
    PREFERRED = "PREFERRED"
    AVOID_IF_POSSIBLE = "AVOID_IF_POSSIBLE"


@dataclass(frozen=True)
class ResourceOperationalSignal:
    """Bounded operational signal derived from local resource readiness.

    This signal is suitable only for local elastic-workload admission and
    non-consensus routing preference.

    It carries no authority over validator membership, signing eligibility,
    voting power, quorum, or finality.
    """

    schema: str
    readiness: ResourceReadiness
    elastic_workload: ElasticWorkloadAdmission
    routing: RoutingPreference

    def __post_init__(self) -> None:
        if self.schema != "hashburst-resource-operational-signal-v1":
            raise ValueError("operational_signal_schema_invalid")


def operational_signal(
    state: ResourceReadinessState,
) -> ResourceOperationalSignal:
    """Map resource readiness to bounded operational behavior."""

    if state.readiness is ResourceReadiness.READY:
        return ResourceOperationalSignal(
            schema="hashburst-resource-operational-signal-v1",
            readiness=ResourceReadiness.READY,
            elastic_workload=ElasticWorkloadAdmission.ALLOW,
            routing=RoutingPreference.PREFERRED,
        )

    if state.readiness is ResourceReadiness.DEGRADED:
        return ResourceOperationalSignal(
            schema="hashburst-resource-operational-signal-v1",
            readiness=ResourceReadiness.DEGRADED,
            elastic_workload=ElasticWorkloadAdmission.THROTTLE,
            routing=RoutingPreference.AVOID_IF_POSSIBLE,
        )

    raise ValueError("resource_readiness_unknown")
