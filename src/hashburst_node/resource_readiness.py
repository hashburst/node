from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Iterable


class ResourceReadiness(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True)
class ResourceObservation:
    """Generic host-resource observation.

    This structure contains operational host telemetry only.  It is
    independent from mining telemetry and carries no consensus authority.
    """

    observed_at: float
    cpu_utilization: float
    memory_utilization: float
    io_utilization: float
    network_utilization: float
    backlog_utilization: float
    provenance: str = "host-resource-observation-v1"

    def __post_init__(self) -> None:
        if not isfinite(self.observed_at) or self.observed_at < 0:
            raise ValueError("observed_at_invalid")

        if not isinstance(self.provenance, str) or not self.provenance:
            raise ValueError("provenance_invalid")

        for name in (
            "cpu_utilization",
            "memory_utilization",
            "io_utilization",
            "network_utilization",
            "backlog_utilization",
        ):
            value = getattr(self, name)

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value < 0.0
                or value > 1.0
            ):
                raise ValueError(f"{name}_invalid")

    @property
    def peak_utilization(self) -> float:
        return max(
            self.cpu_utilization,
            self.memory_utilization,
            self.io_utilization,
            self.network_utilization,
            self.backlog_utilization,
        )


@dataclass(frozen=True)
class ResourceReadinessPolicy:
    """Operational READY/DEGRADED policy with hysteresis.

    The policy may be consumed by local workload admission/throttling and
    non-consensus routing.

    It MUST NOT determine validator membership, signing eligibility, quorum,
    consensus voting power, or finality.
    """

    degrade_threshold: float = 0.90
    recover_threshold: float = 0.75
    degrade_observations: int = 3
    recover_observations: int = 3

    def __post_init__(self) -> None:
        for name in ("degrade_threshold", "recover_threshold"):
            value = getattr(self, name)

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value < 0.0
                or value > 1.0
            ):
                raise ValueError(f"{name}_invalid")

        if self.recover_threshold >= self.degrade_threshold:
            raise ValueError("hysteresis_invalid")

        for name in ("degrade_observations", "recover_observations"):
            value = getattr(self, name)

            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name}_invalid")


@dataclass(frozen=True)
class ResourceReadinessState:
    readiness: ResourceReadiness = ResourceReadiness.READY
    consecutive_pressure: int = 0
    consecutive_recovery: int = 0


def evaluate_resource_readiness(
    previous: ResourceReadinessState,
    observation: ResourceObservation,
    policy: ResourceReadinessPolicy,
) -> ResourceReadinessState:
    """Advance operational readiness by one observation.

    The transition is deterministic for the same previous state,
    observation and policy.

    No blockchain, validator, mining, networking or filesystem mutation is
    performed here.
    """

    peak = observation.peak_utilization

    if previous.readiness is ResourceReadiness.READY:
        pressure = (
            previous.consecutive_pressure + 1
            if peak >= policy.degrade_threshold
            else 0
        )

        if pressure >= policy.degrade_observations:
            return ResourceReadinessState(
                readiness=ResourceReadiness.DEGRADED,
                consecutive_pressure=0,
                consecutive_recovery=0,
            )

        return ResourceReadinessState(
            readiness=ResourceReadiness.READY,
            consecutive_pressure=pressure,
            consecutive_recovery=0,
        )

    recovery = (
        previous.consecutive_recovery + 1
        if peak <= policy.recover_threshold
        else 0
    )

    if recovery >= policy.recover_observations:
        return ResourceReadinessState(
            readiness=ResourceReadiness.READY,
            consecutive_pressure=0,
            consecutive_recovery=0,
        )

    return ResourceReadinessState(
        readiness=ResourceReadiness.DEGRADED,
        consecutive_pressure=0,
        consecutive_recovery=recovery,
    )


def evaluate_observations(
    observations: Iterable[ResourceObservation],
    policy: ResourceReadinessPolicy,
    initial: ResourceReadinessState | None = None,
) -> ResourceReadinessState:
    state = initial or ResourceReadinessState()

    for observation in observations:
        state = evaluate_resource_readiness(state, observation, policy)

    return state
