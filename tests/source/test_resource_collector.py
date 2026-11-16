from pathlib import Path

import pytest

from hashburst_node.resource_collector import (
    LinuxResourceSample,
    observation_from_samples,
    read_linux_resource_sample,
)


def write_fake_proc(root: Path):
    (root / "net").mkdir(parents=True)

    (root / "stat").write_text(
        "cpu  100 0 50 850 0 0 0 0 0 0\n",
        encoding="utf-8",
    )

    (root / "meminfo").write_text(
        "MemTotal:       1000 kB\n"
        "MemFree:         100 kB\n"
        "MemAvailable:    250 kB\n"
        "Buffers:          50 kB\n"
        "Cached:          100 kB\n",
        encoding="utf-8",
    )

    (root / "diskstats").write_text(
        "8 0 sda 1 0 0 0 1 0 0 0 0 400 0 0 0 0 0\n",
        encoding="utf-8",
    )

    (root / "net" / "dev").write_text(
        "Inter-| Receive | Transmit\n"
        " face |bytes packets errs drop fifo frame compressed multicast "
        "|bytes packets errs drop fifo colls carrier compressed\n"
        "lo: 999 0 0 0 0 0 0 0 999 0 0 0 0 0 0 0\n"
        "eth0: 1000 0 0 0 0 0 0 0 2000 0 0 0 0 0 0 0\n",
        encoding="utf-8",
    )


def test_read_linux_resource_sample_from_synthetic_proc(tmp_path):
    write_fake_proc(tmp_path)

    sample = read_linux_resource_sample(tmp_path)

    assert sample.cpu_total == 1000
    assert sample.cpu_idle == 850
    assert sample.memory_utilization == pytest.approx(0.75)
    assert sample.disk_total == 400
    assert sample.network_total == 3000


def test_observation_from_samples_is_deterministic():
    before = LinuxResourceSample(
        cpu_total=1000,
        cpu_idle=800,
        disk_total=100,
        network_total=1000,
        memory_utilization=0.40,
    )

    after = LinuxResourceSample(
        cpu_total=1100,
        cpu_idle=820,
        disk_total=600,
        network_total=51_000,
        memory_utilization=0.60,
    )

    obs = observation_from_samples(
        before,
        after,
        elapsed_seconds=1.0,
        observed_at=123.0,
        backlog_utilization=0.25,
        disk_capacity_ms_per_second=1000.0,
        network_capacity_bytes_per_second=100_000.0,
    )

    assert obs.cpu_utilization == pytest.approx(0.80)
    assert obs.memory_utilization == pytest.approx(0.60)
    assert obs.io_utilization == pytest.approx(0.50)
    assert obs.network_utilization == pytest.approx(0.50)
    assert obs.backlog_utilization == pytest.approx(0.25)
    assert obs.observed_at == 123.0
    assert obs.provenance == "linux-proc-resource-observation-v1"


def test_io_and_network_are_clamped():
    before = LinuxResourceSample(
        cpu_total=100,
        cpu_idle=50,
        disk_total=0,
        network_total=0,
        memory_utilization=0.10,
    )

    after = LinuxResourceSample(
        cpu_total=200,
        cpu_idle=60,
        disk_total=5000,
        network_total=5000,
        memory_utilization=0.20,
    )

    obs = observation_from_samples(
        before,
        after,
        elapsed_seconds=1.0,
        observed_at=1.0,
        disk_capacity_ms_per_second=1000.0,
        network_capacity_bytes_per_second=1000.0,
    )

    assert obs.io_utilization == 1.0
    assert obs.network_utilization == 1.0


@pytest.mark.parametrize(
    "elapsed,disk_capacity,network_capacity",
    [
        (0.0, 1000.0, 1000.0),
        (-1.0, 1000.0, 1000.0),
        (1.0, 0.0, 1000.0),
        (1.0, 1000.0, 0.0),
    ],
)
def test_invalid_capacity_or_elapsed_fails_closed(
    elapsed,
    disk_capacity,
    network_capacity,
):
    before = LinuxResourceSample(100, 50, 0, 0, 0.1)
    after = LinuxResourceSample(200, 60, 1, 1, 0.1)

    with pytest.raises(ValueError):
        observation_from_samples(
            before,
            after,
            elapsed_seconds=elapsed,
            observed_at=1.0,
            disk_capacity_ms_per_second=disk_capacity,
            network_capacity_bytes_per_second=network_capacity,
        )


def test_counter_regression_fails_closed():
    before = LinuxResourceSample(
        cpu_total=100,
        cpu_idle=50,
        disk_total=100,
        network_total=100,
        memory_utilization=0.10,
    )

    after = LinuxResourceSample(
        cpu_total=200,
        cpu_idle=60,
        disk_total=99,
        network_total=100,
        memory_utilization=0.10,
    )

    with pytest.raises(ValueError, match="disk_sample_delta_invalid"):
        observation_from_samples(
            before,
            after,
            elapsed_seconds=1.0,
            observed_at=1.0,
        )


def test_loopback_is_excluded_from_network_total(tmp_path):
    write_fake_proc(tmp_path)

    (tmp_path / "net" / "dev").write_text(
        "Inter-| Receive | Transmit\n"
        " face |bytes packets errs drop fifo frame compressed multicast "
        "|bytes packets errs drop fifo colls carrier compressed\n"
        "lo: 500000 0 0 0 0 0 0 0 500000 0 0 0 0 0 0 0\n"
        "eth0: 100 0 0 0 0 0 0 0 200 0 0 0 0 0 0 0\n",
        encoding="utf-8",
    )

    sample = read_linux_resource_sample(tmp_path)

    assert sample.network_total == 300
