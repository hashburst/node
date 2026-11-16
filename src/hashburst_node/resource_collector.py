from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic, sleep
from typing import Callable

from hashburst_node.resource_readiness import ResourceObservation


@dataclass(frozen=True)
class LinuxResourceSample:
    cpu_total: int
    cpu_idle: int
    disk_total: int
    network_total: int
    memory_utilization: float


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _read_cpu(proc: Path) -> tuple[int, int]:
    fields = (proc / "stat").read_text(
        encoding="utf-8"
    ).splitlines()[0].split()

    if not fields or fields[0] != "cpu":
        raise RuntimeError("proc_cpu_invalid")

    values = [int(value) for value in fields[1:]]

    if len(values) < 4:
        raise RuntimeError("proc_cpu_incomplete")

    total = sum(values)
    idle = values[3]

    if len(values) > 4:
        idle += values[4]

    return total, idle


def _read_memory(proc: Path) -> float:
    values = {}

    for line in (proc / "meminfo").read_text(
        encoding="utf-8"
    ).splitlines():
        if ":" not in line:
            continue

        key, raw = line.split(":", 1)
        parts = raw.strip().split()

        if parts:
            values[key] = int(parts[0])

    total = values.get("MemTotal", 0)

    if total <= 0:
        raise RuntimeError("proc_memory_invalid")

    available = values.get("MemAvailable")

    if available is None:
        available = (
            values.get("MemFree", 0)
            + values.get("Buffers", 0)
            + values.get("Cached", 0)
        )

    return _clamp(1.0 - (available / total))


def _read_disk(proc: Path) -> int:
    total_ms = 0

    for line in (proc / "diskstats").read_text(
        encoding="utf-8"
    ).splitlines():
        fields = line.split()

        if len(fields) < 13:
            continue

        try:
            total_ms += int(fields[12])
        except ValueError:
            continue

    return total_ms


def _read_network(proc: Path) -> int:
    total = 0

    lines = (proc / "net" / "dev").read_text(
        encoding="utf-8"
    ).splitlines()

    for line in lines[2:]:
        if ":" not in line:
            continue

        interface, raw = line.split(":", 1)

        if interface.strip() == "lo":
            continue

        fields = raw.split()

        if len(fields) < 9:
            continue

        try:
            total += int(fields[0])
            total += int(fields[8])
        except ValueError:
            continue

    return total


def read_linux_resource_sample(
    proc_root: str | Path = "/proc",
) -> LinuxResourceSample:
    proc = Path(proc_root)

    cpu_total, cpu_idle = _read_cpu(proc)

    return LinuxResourceSample(
        cpu_total=cpu_total,
        cpu_idle=cpu_idle,
        disk_total=_read_disk(proc),
        network_total=_read_network(proc),
        memory_utilization=_read_memory(proc),
    )


def observation_from_samples(
    before: LinuxResourceSample,
    after: LinuxResourceSample,
    *,
    elapsed_seconds: float,
    observed_at: float,
    backlog_utilization: float = 0.0,
    disk_capacity_ms_per_second: float = 1000.0,
    network_capacity_bytes_per_second: float = 125_000_000.0,
) -> ResourceObservation:
    if elapsed_seconds <= 0:
        raise ValueError("elapsed_seconds_invalid")

    if disk_capacity_ms_per_second <= 0:
        raise ValueError("disk_capacity_invalid")

    if network_capacity_bytes_per_second <= 0:
        raise ValueError("network_capacity_invalid")

    cpu_delta = after.cpu_total - before.cpu_total
    idle_delta = after.cpu_idle - before.cpu_idle

    if cpu_delta <= 0 or idle_delta < 0:
        raise ValueError("cpu_sample_delta_invalid")

    disk_delta = after.disk_total - before.disk_total
    network_delta = after.network_total - before.network_total

    if disk_delta < 0:
        raise ValueError("disk_sample_delta_invalid")

    if network_delta < 0:
        raise ValueError("network_sample_delta_invalid")

    cpu_utilization = _clamp(
        1.0 - (idle_delta / cpu_delta)
    )

    io_utilization = _clamp(
        disk_delta
        / (elapsed_seconds * disk_capacity_ms_per_second)
    )

    network_utilization = _clamp(
        network_delta
        / (elapsed_seconds * network_capacity_bytes_per_second)
    )

    return ResourceObservation(
        observed_at=observed_at,
        cpu_utilization=cpu_utilization,
        memory_utilization=after.memory_utilization,
        io_utilization=io_utilization,
        network_utilization=network_utilization,
        backlog_utilization=backlog_utilization,
        provenance="linux-proc-resource-observation-v1",
    )


def collect_linux_resource_observation(
    *,
    interval_seconds: float = 0.25,
    backlog_utilization: float = 0.0,
    proc_root: str | Path = "/proc",
    sleeper: Callable[[float], None] = sleep,
    clock: Callable[[], float] = monotonic,
) -> ResourceObservation:
    if interval_seconds <= 0:
        raise ValueError("interval_seconds_invalid")

    before = read_linux_resource_sample(proc_root)

    started = clock()
    sleeper(interval_seconds)
    finished = clock()

    elapsed = finished - started

    if elapsed <= 0:
        raise RuntimeError("collector_clock_invalid")

    after = read_linux_resource_sample(proc_root)

    return observation_from_samples(
        before,
        after,
        elapsed_seconds=elapsed,
        observed_at=finished,
        backlog_utilization=backlog_utilization,
    )
