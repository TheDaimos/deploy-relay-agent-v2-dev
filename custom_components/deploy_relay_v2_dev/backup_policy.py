"""V2-only backup retention planner: pure, no removal and no V1 access."""
from __future__ import annotations

from datetime import datetime

MIN_KEEP = 3
MAX_KEEP = 100
MAX_BACKUPS = 512


class BackupPolicyError(ValueError):
    """Strict retention planning failure."""


def rotation_plan(project_id: str, snapshots: object, *, keep: int,
                  protected: frozenset[str] = frozenset()) -> tuple[str, ...]:
    """List independently verified owned snapshots eligible for later pruning.

    No filesystem access or deletion. Incomplete, unverified and recovery
    snapshots are always protected. The future transaction engine must verify
    actual backup files and hashes independently before it uses this plan.
    """
    if type(project_id) is not str or not project_id or not project_id.isascii():
        raise BackupPolicyError("invalid project identity")
    if type(keep) is not int or not MIN_KEEP <= keep <= MAX_KEEP:
        raise BackupPolicyError("invalid retention")
    if type(snapshots) is not list or len(snapshots) > MAX_BACKUPS:
        raise BackupPolicyError("invalid backup inventory")
    if type(protected) is not frozenset or any(type(x) is not str for x in protected):
        raise BackupPolicyError("invalid protection set")
    eligible = []
    seen = set()
    for row in snapshots:
        if type(row) is not dict or set(row) != {
            "backup_id", "project_id", "created_at", "complete",
            "verified", "active_recovery",
        }:
            raise BackupPolicyError("invalid backup descriptor")
        ident = row["backup_id"]
        if type(ident) is not str or len(ident) > 100 or not ident.isascii() or not ident or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in ident
        ):
            raise BackupPolicyError("invalid backup identifier")
        if ident in seen:
            raise BackupPolicyError("duplicate backup")
        seen.add(ident)
        if row["project_id"] != project_id:
            raise BackupPolicyError("cross-project backup")
        if any(type(row[key]) is not bool for key in ("complete", "verified", "active_recovery")):
            raise BackupPolicyError("invalid backup verification")
        stamp = row["created_at"]
        if type(stamp) is not str or len(stamp) != 20:
            raise BackupPolicyError("invalid backup timestamp")
        try:
            parsed = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise BackupPolicyError("invalid backup timestamp") from None
        if row["complete"] and row["verified"] and not row["active_recovery"] and ident not in protected:
            eligible.append((parsed, ident))
    eligible.sort(key=lambda x: (x[0], x[1]))
    verified_total = sum(
        row["complete"] and row["verified"] for row in snapshots
    )
    prune_max = max(0, verified_total - keep)
    return tuple(ident for _, ident in eligible[:prune_max])
