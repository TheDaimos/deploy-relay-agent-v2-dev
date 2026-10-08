"""Opt-in, bounded, synthetic V2 DEV measurement. No project or file access.

Process-wide CPU figures are explicitly *not* DRA-only CPU measurements.
No measurements are stored in the durable operation journal.
"""
from __future__ import annotations

import hashlib
import time
from asyncio import sleep, to_thread, wait_for
from collections.abc import Awaitable, Callable

from .operation_model import OperationPhase

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
        self._summary = {
            "operation_id": self._operation_id,
            "schema": "dra-v2-dev-measurement.v1",
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
        }
