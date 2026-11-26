"""G3-10: conservative read-only presence observation of HA target roots.

This module does NOT identify a file owner, perform a V1/V2 handover, or
implement an inter-process lock. Even confirmed absence is NEVER ownership
proof. All returned states are exclusively informational and fail closed.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
import stat

from .source_preflight import PreflightError, target_path

SCHEMA = "dra-v2-dev-target-presence.v1"
MAX_TARGETS = 32
MAX_DIRECTORY_ENTRIES = 2048
_VALID_PRESENCE = frozenset({"present", "absent", "ambiguous", "unsafe", "unavailable"})


class TargetPresenceError(ValueError):
    """Generic, non-secret read-only observation failure."""


def _validate_targets(targets: object) -> list[str]:
    if type(targets) not in (list, tuple) or not 1 <= len(targets) <= MAX_TARGETS:
        raise TargetPresenceError("invalid target collection")
    unique: set[str] = set()
    normalized: list[str] = []
    for candidate in targets:
        try:
            target = target_path(candidate)
        except PreflightError:
            raise TargetPresenceError("invalid target") from None
        if target.casefold() in unique:
            raise TargetPresenceError("duplicate target identity")
        unique.add(target.casefold())
        normalized.append(target)
    return normalized


def _open_directory(path: object, *, dir_fd: int | None = None) -> int:
    if not isinstance(path, (str, bytes, os.PathLike)):
        raise TargetPresenceError("invalid source directory")
    if isinstance(path, str) and not path:
        raise TargetPresenceError("invalid source directory")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW |
                     getattr(os, "O_CLOEXEC", 0), dir_fd=dir_fd)
    except OSError:
        raise TargetPresenceError("directory cannot be verified") from None
    if not stat.S_ISDIR(os.fstat(fd).st_mode):
        os.close(fd)
        raise TargetPresenceError("directory cannot be verified")
    return fd


def observe_target_presence(config_root: object, targets: object) -> dict[str, object]:
    """Inspect bounded directory entries without opening project files.

    The caller must supply the server-owned HA configuration root and a
    backend-generated set of target roots. No browser paths or preview
    authorization may be accepted here. This observation cannot rule out
    a simultaneous V1 update or external process writing after inspection.
    """
    requested = _validate_targets(targets)
    root_fd = _open_directory(config_root)
    try:
        components_fd = _open_directory("custom_components", dir_fd=root_fd)
        try:
            try:
                all_names = os.listdir(components_fd)
            except OSError:
                raise TargetPresenceError("directory cannot be listed") from None
            if len(all_names) > MAX_DIRECTORY_ENTRIES:
                raise TargetPresenceError("directory listing limit exceeded")
            # Only names of the managed integration roots are considered.
            # Never read metadata from .storage, V1 private files or backups.
            actual_names = {}
            for name in all_names:
                if type(name) is not str:
                    raise TargetPresenceError("invalid directory entry")
                actual_names.setdefault(name.casefold(), []).append(name)

            observed = []
            for target in requested:
                leaf = target.split("/", 1)[1]
                candidates = actual_names.get(leaf.casefold(), [])
                if not candidates:
                    presence = "absent"
                elif len(candidates) > 1:
                    presence = "ambiguous"
                else:
                    try:
                        info = os.stat(candidates[0], dir_fd=components_fd,
                                       follow_symlinks=False)
                    except OSError:
                        presence = "unavailable"
                    else:
                        presence = "present" if stat.S_ISDIR(info.st_mode) else "unsafe"
                observed.append({"target": target, "presence": presence,
                                 "ownership": "unverified"})
        finally:
            os.close(components_fd)
    finally:
        os.close(root_fd)
    return {
        "schema": SCHEMA,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "inspection": "local_directories_only",
        "target_count": len(observed),
        "targets": observed,
        "owner_identity_verified": False,
        "v1_handover_verified": False,
        "cross_process_lock_verified": False,
        "backup_verified": False,
        "source_binding_verified": False,
        "handover_required": True,
        "installation_enabled": False,
        "parallel_installation_enabled": False,
    }
