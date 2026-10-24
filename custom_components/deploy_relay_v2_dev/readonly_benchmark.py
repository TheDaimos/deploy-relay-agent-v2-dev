"""Opt-in, bounded, synthetic V2 DEV measurement. No project or file access.

Process-wide CPU figures are explicitly *not* DRA-only CPU measurements.
No measurements are stored in the durable operation journal.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import sys
import time
from asyncio import sleep, to_thread, wait_for
from collections.abc import Awaitable, Callable

from .operation_model import OperationPhase
import re

MEMORY_SOURCE = "LINUX_PROCFS_VISIBLE_TO_HA"

SNAPSHOT_FIELDS = (
    "total_kib", "used_effective_kib", "free_kib", "available_kib",
    "ha_process_rss_kib",
)
MAX_KIB = 1 << 44
_LINE = re.compile(r"^(MemTotal|MemAvailable|MemFree|VmRSS):\s+([0-9]+)\s+kB\s*$")
_MEMINFO = "/proc/meminfo"
_STATUS = "/proc/self/status"


def _read_fields(path: str, wanted: frozenset[str]) -> dict[str, int]:
    try:
        # Small, hard-capped read; never open user-selected files.
        with open(path, "r", encoding="ascii") as source:
            raw = source.read(16384)
    except (OSError, UnicodeError):
        return {}
    values: dict[str, int] = {}
    for line in raw.splitlines():
        match = _LINE.fullmatch(line)
        if match is None or match[1] not in wanted or match[1] in values:
            continue
        number = int(match[2])
        if 0 <= number <= MAX_KIB:
            values[match[1]] = number
    return values


def snapshot_memory() -> dict[str, int | None]:
    """Bounded four-point Linux memory sample; worker only, never idle."""
    mem = _read_fields(_MEMINFO, frozenset({"MemTotal", "MemAvailable", "MemFree"}))
    process = _read_fields(_STATUS, frozenset({"VmRSS"}))
    total, available, free = (
        mem.get("MemTotal"), mem.get("MemAvailable"), mem.get("MemFree"),
    )
    if (
        total is None or total <= 0 or available is None or free is None
        or available > total or free > total
    ):
        total = available = free = used = None
    else:
        used = total - available  # Includes real pressure, not merely MemFree.
    return {
        "total_kib": total,
        "used_effective_kib": used,
        "free_kib": free,
        "available_kib": available,
        "ha_process_rss_kib": process.get("VmRSS"),
    }

STEPS = 40
BASE_STEPS = 10
WORK_STEPS = 20
SAMPLE_BYTES = b"V2_DEV_MEASUREMENT_ONLY_" * 2731  # fixed ~64 KiB


def _bounded_synthetic_hash() -> int:
    """Single worker; <=32 passes and <=40ms wall-time, not on HA event loop."""
    deadline = time.perf_counter() + 0.040
    processed = 0
    while processed < 32 and time.perf_counter() < deadline:
        hashlib.sha256(SAMPLE_BYTES).digest()
        processed += 1
    return processed


class ReadOnlyMeasurement:
    """At most the latest in-memory summary; no idle timers or data persistence."""

    def __init__(self) -> None:
        self._operation_id: str | None = None
        self._summary: dict[str, object] | None = None

    def claim(self, operation_id: str) -> None:
        if not isinstance(operation_id, str) or len(operation_id) != 32:
            raise ValueError("invalid measurement operation")
        self._operation_id = operation_id
        self._summary = None

    def summary(self) -> dict[str, object] | None:
        return self._summary.copy() if self._summary is not None else None

    async def run(
        self,
        progress: Callable[[OperationPhase, int, int], Awaitable[None]],
    ) -> None:
        """10s baseline, 20s bounded synthetic workload, 10s post-run.

        Only the existing read-only owner can start this work, using the same
        operation journal and concurrency cap. Tests may patch the module-local
        sleep/to_thread to avoid waiting for wall time.
        """
        phase_cpu = [0, 0, 0]
        phase_seconds = [0, 0, 0]
        samples = 0
        max_scheduler_lag_ms = 0
        start = time.monotonic()
        memory = {"start": await to_thread(snapshot_memory)}
        for index in range(1, STEPS + 1):
            stage = 0 if index <= BASE_STEPS else (1 if index <= BASE_STEPS + WORK_STEPS else 2)
            began = time.monotonic()
            cpu_before = time.process_time_ns()
            await sleep(1)
            lag_ms = max(0, int((time.monotonic() - began - 1) * 1000))
            max_scheduler_lag_ms = max(max_scheduler_lag_ms, lag_ms)
            if stage == 1:
                # Small, deterministic, non-project workload in one executor
                # thread; the Home Assistant event loop is never CPU-busy.
                samples += await wait_for(to_thread(_bounded_synthetic_hash), timeout=1.0)
            await progress(OperationPhase.INVENTORY, index, STEPS)
            phase_cpu[stage] += max(0, (time.process_time_ns() - cpu_before) // 1_000_000)
            phase_seconds[stage] += 1
            if index == BASE_STEPS:
                memory["base_end"] = await to_thread(snapshot_memory)
            elif index == BASE_STEPS + WORK_STEPS:
                memory["work_end"] = await to_thread(snapshot_memory)
            elif index == STEPS:
                memory["end"] = await to_thread(snapshot_memory)
        self._summary = {
            "operation_id": self._operation_id,
            "schema": "dra-v2-dev-measurement.v2",
            "base_process_cpu_ms": phase_cpu[0],
            "work_process_cpu_ms": phase_cpu[1],
            "after_process_cpu_ms": phase_cpu[2],
            "base_seconds": phase_seconds[0],
            "work_seconds": phase_seconds[1],
            "after_seconds": phase_seconds[2],
            "max_wakeup_delay_ms": min(max_scheduler_lag_ms, 60000),
            "synthetic_hashes": samples,
            "elapsed_ms": min(int((time.monotonic() - start) * 1000), 3600000),
            "scope": "HA_PROCESS_WIDE_CPU_NOT_DRA_ONLY",
            "memory": {
                "schema": "dra-v2-dev-memory.v1",
                "source": MEMORY_SOURCE,
                "snapshots": memory,
                "component_memory": {
                    "dra_v1_kib": None,
                    "dra_v2_kib": None,
                    "reason": "SHARED_HA_PROCESS_CANNOT_ATTRIBUTE",
                },
            },
        }


# Explicitly triggered synthetic multiprocess check; no HA or project imports
# occur in the short-lived children. At most twelve processes at any instant.
MULTICORE_WORKERS = (1, 2, 4, 6, 8, 10, 12)
MULTICORE_ITERATIONS = 400000
MULTICORE_TIMEOUT_SECONDS = 4
SUITE_TOTAL_STEPS = 40 + 40 + len(MULTICORE_WORKERS)
_WORKER_CODE = (
    "import hashlib,json,time\n"
    "start=time.monotonic_ns(); cpu=time.process_time_ns()\n"
    "hashlib.pbkdf2_hmac('sha256',b'dra-v2-dev-synthetic-only',"
    "b'fixed-salt',400000)\n"
    "print(json.dumps({'wall_ms':(time.monotonic_ns()-start)//1000000,"
    "'cpu_ms':(time.process_time_ns()-cpu)//1000000,'iterations':400000}))\n"
)


async def _single_multicore_stage(workers: int) -> dict[str, object]:
    """Start only fixed Python workers; terminate and reap on every exit path."""
    if workers not in MULTICORE_WORKERS:
        raise ValueError("invalid worker count")
    children = []
    started = time.monotonic()
    rows: list[dict[str, int]] = []
    status = "unavailable"
    try:
        for _ in range(workers):
            child = await asyncio.create_subprocess_exec(
                sys.executable, "-I", "-S", "-c", _WORKER_CODE,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                env={"PYTHONHASHSEED": "0"},
                close_fds=True,
            )
            children.append(child)
        raw_results = await asyncio.wait_for(
            asyncio.gather(*(p.communicate() for p in children)),
            timeout=MULTICORE_TIMEOUT_SECONDS,
        )
        import json
        for child, (out, _err) in zip(children, raw_results):
            if child.returncode != 0 or len(out) > 512:
                raise ValueError("synthetic worker returned an invalid result")
            result = json.loads(out.decode("ascii"))
            if (type(result) is not dict or set(result) != {"wall_ms", "cpu_ms", "iterations"}
                or type(result["wall_ms"]) is not int
                or type(result["cpu_ms"]) is not int
                or result["iterations"] != MULTICORE_ITERATIONS
                or not 0 <= result["wall_ms"] <= MULTICORE_TIMEOUT_SECONDS * 1000
                or not 0 <= result["cpu_ms"] <= MULTICORE_TIMEOUT_SECONDS * 1000):
                raise ValueError("invalid synthetic worker timings")
            rows.append(result)
        status = "ok"
    except asyncio.CancelledError:
        raise
    except (OSError, RuntimeError, ValueError, UnicodeError, asyncio.TimeoutError):
        status = "unavailable"
    finally:
        for child in children:
            if child.returncode is None:
                try:
                    child.kill()
                except ProcessLookupError:
                    pass
        for child in children:
            try:
                await asyncio.wait_for(child.wait(), timeout=2)
            except (OSError, asyncio.TimeoutError):
                pass
    elapsed = min(max(0, int((time.monotonic()-started)*1000)), 30000)
    return {
        "workers": workers,
        "status": status,
        "wall_ms": elapsed if status == "ok" else None,
        "aggregate_worker_cpu_ms": sum(x["cpu_ms"] for x in rows) if status == "ok" else None,
        "iterations_total": workers * MULTICORE_ITERATIONS if status == "ok" else None,
    }


async def _multiprocess_diagnostics(
    progress: Callable[[int], Awaitable[None]],
) -> dict[str, object]:
    """No configurable process counts, no network, no HA event-loop CPU stress."""
    cpu_visible: int | None = None
    affinity_visible: int | None = None
    try:
        value = os.cpu_count()
        if type(value) is int and 1 <= value <= 1024:
            cpu_visible = value
        if hasattr(os, "sched_getaffinity"):
            affinity = len(os.sched_getaffinity(0))
            if type(affinity) is int and 1 <= affinity <= 1024:
                affinity_visible = affinity
    except (OSError, AttributeError, ValueError):
        pass
    levels = []
    for index, workers in enumerate(MULTICORE_WORKERS, 1):
        # If affinity is below this stage, report unavailable, never overload.
        if affinity_visible is not None and affinity_visible < workers:
            result = {
                "workers": workers, "status": "unavailable", "wall_ms": None,
                "aggregate_worker_cpu_ms": None, "iterations_total": None,
            }
        else:
            result = await _single_multicore_stage(workers)
        levels.append(result)
        await progress(index)
    return {
        "schema": "dra-v2-dev-multicore.v2",
        "method": "BOUNDED_CHILD_PROCESSES",
        "logical_cpus_visible": cpu_visible,
        "affinity_cpus_visible": affinity_visible,
        "levels": levels,
    }


class ReadOnlySuite:
    """One HA-owned, read-only task. Volatile report, no auto-start or retry."""

    def __init__(self, measurement: ReadOnlyMeasurement) -> None:
        self._measurement = measurement
        self._operation_id: str | None = None
        self._summary: dict[str, object] | None = None

    def claim(self, operation_id: str) -> None:
        if not isinstance(operation_id, str) or len(operation_id) != 32:
            raise ValueError("invalid suite operation id")
        self._operation_id = operation_id
        self._summary = None

    def summary(self) -> dict[str, object] | None:
        return self._summary.copy() if self._summary is not None else None

    async def run_all(self, progress: Callable[[OperationPhase, int, int], Awaitable[None]]) -> None:
        """40s preview, 40s CPU/RAM run, then 1/2/4/6/8/10/12."""
        self._summary = None
        self._measurement.claim(str(self._operation_id))
        for index in range(1, 41):
            await sleep(1)
            await progress(OperationPhase.INVENTORY, index, SUITE_TOTAL_STEPS)

        async def measurement_progress(phase, current, _total):
            await progress(phase, 40 + current, SUITE_TOTAL_STEPS)
        await self._measurement.run(measurement_progress)

        async def multicore_progress(index):
            await progress(OperationPhase.INVENTORY, 80 + index, SUITE_TOTAL_STEPS)
        multicore = await _multiprocess_diagnostics(multicore_progress)
        result = self._measurement.summary()
        if result is None:
            raise ValueError("measurement result missing")
        self._summary = {
            "schema": "dra-v2-dev-suite.v2",
            "operation_id": self._operation_id,
            "mode": "full",
            "readonly_steps": 40,
            "measurement": result,
            "multicore": multicore,
        }

    async def run_multicore(
        self, progress: Callable[[OperationPhase, int, int], Awaitable[None]],
    ) -> None:
        """Dedicated 1/2/4/6/8/10/12 diagnostics, without prior wait."""
        self._summary = None
        async def multicore_progress(index):
            await progress(OperationPhase.INVENTORY, index, len(MULTICORE_WORKERS))
        multicore = await _multiprocess_diagnostics(multicore_progress)
        self._summary = {
            "schema": "dra-v2-dev-suite.v2",
            "operation_id": self._operation_id,
            "mode": "multicore",
            "readonly_steps": 0,
            "measurement": None,
            "multicore": multicore,
        }
