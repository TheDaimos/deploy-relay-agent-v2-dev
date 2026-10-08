"""Bounded Linux /proc memory counters for optional synthetic measurements.

All reads target two fixed kernel pseudo-files. No Home Assistant configuration
or integration objects are accessed, and no collector runs while idle.
This is guest/container-visible memory, *not* Proxmox guest accounting.
"""
from __future__ import annotations

import re

SOURCE = "LINUX_PROCFS_VISIBLE_TO_HA"
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
    """One synchronous, bounded sample. Invoke in a worker only when requested."""
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
