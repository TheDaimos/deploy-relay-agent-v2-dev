"""V2-only project catalog: opt-in V1 metadata import, no V1 writes/secrets."""
from __future__ import annotations

import asyncio
import re
from typing import Protocol

SCHEMA = "dra-v2-dev-projects.v1"
DEFAULT_RETENTION = 10
MIN_RETENTION = 3
MAX_RETENTION = 100
MAX_PROJECTS = 32
_NAME = re.compile(r"^[^\x00-\x1f\x7f<>]{1,80}\Z")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}\Z")
_PROJECT_ID = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_MANIFEST = "deploy-relay.json"
_ENTRY_KEYS = frozenset({
    "project_id", "name", "repository", "manifest_path",
    "origin", "status", "backup_retention",
})


class CatalogError(ValueError):
    """Safe catalog error without credentials."""


class CatalogStore(Protocol):
    async def async_load(self) -> object: ...
    async def async_save(self, value: dict[str, object]) -> None: ...


def normalize_repo(repository: object) -> str:
    if type(repository) is not str:
        raise CatalogError("invalid repository")
    value = repository.strip()
    if value.startswith("https://github.com/"):
        value = value[len("https://github.com/"):]
    if value.endswith(".git"):
        value = value[:-4]
    if not _REPOSITORY.fullmatch(value):
        raise CatalogError("invalid repository")
    owner, name = value.split("/", 1)
    if owner in (".", "..") or name in (".", ".."):
        raise CatalogError("invalid repository")
    return value


def sanitize_entry(row: object) -> dict[str, object]:
    if type(row) is not dict or set(row) != _ENTRY_KEYS:
        raise CatalogError("invalid project record")
    repo = normalize_repo(row["repository"])
    if type(row["project_id"]) is not str or not _PROJECT_ID.fullmatch(row["project_id"]):
        raise CatalogError("invalid project identity")
    name = row["name"]
    if type(name) is not str or not _NAME.fullmatch(name) or name.strip() != name:
        raise CatalogError("invalid project label")
    if row["manifest_path"] != _MANIFEST:
        raise CatalogError("unsupported manifest")
    if row["origin"] not in ("v1_import", "manual") or type(row["origin"]) is not str:
        raise CatalogError("invalid project origin")
    if row["status"] != "pending_review":
        raise CatalogError("invalid project status")
    retention = row["backup_retention"]
    if type(retention) is not int or not MIN_RETENTION <= retention <= MAX_RETENTION:
        raise CatalogError("invalid backup retention")
    return {
        "project_id": row["project_id"], "name": name, "repository": repo,
        "manifest_path": _MANIFEST, "origin": row["origin"],
        "status": "pending_review", "backup_retention": retention,
    }


def proposal(repository: object, name: object, retention: object = 10,
             *, origin: str) -> dict[str, object]:
    repo = normalize_repo(repository)
    label = name if type(name) is str and name.strip() else repo.split("/")[1]
    if type(label) is not str:
        raise CatalogError("invalid project label")
    ident = re.sub(r"[^a-z0-9_]", "_", repo.split("/")[1].casefold()).strip("_")
    ident = ident[:55] or "project"
    if not ident[0].isalpha():
        ident = "project_" + ident
    if not _PROJECT_ID.fullmatch(ident):
        raise CatalogError("invalid project identity")
    return sanitize_entry({
        "project_id": ident, "name": label.strip(), "repository": repo,
        "manifest_path": _MANIFEST, "origin": origin,
        "status": "pending_review", "backup_retention": retention,
    })


def v1_proposals(config_entries: object) -> list[dict[str, object]]:
    """Read only known V1 subentry fields; never copy access tokens."""
    try:
        v1_entries = config_entries.async_entries("deploy_relay")
    except (AttributeError, TypeError, ValueError):
        raise CatalogError("V1 inventory unavailable") from None
    if not isinstance(v1_entries, (list, tuple)):
        raise CatalogError("V1 inventory unavailable")
    records: dict[str, dict[str, object]] = {}
    for entry in v1_entries:
        subentries = getattr(entry, "subentries", None)
        if not isinstance(subentries, dict):
            continue
        for sub in subentries.values():
            if getattr(sub, "subentry_type", None) != "project":
                continue
            data = getattr(sub, "data", None)
            if not isinstance(data, dict):
                raise CatalogError("V1 project metadata unavailable")
            candidate = proposal(
                data.get("repository"),
                data.get("project_name") or getattr(sub, "title", None),
                data.get("backup_retention", DEFAULT_RETENTION),
                origin="v1_import",
            )
            key = candidate["repository"].casefold()
            if key in records:
                raise CatalogError("duplicate V1 project")
            records[key] = candidate
            if len(records) > MAX_PROJECTS:
                raise CatalogError("V1 catalog too large")
    return sorted(records.values(), key=lambda row: row["repository"].casefold())


class ProjectCatalog:
    def __init__(self, store: CatalogStore) -> None:
        self._store = store
        self._lock = asyncio.Lock()
        self._records: list[dict[str, object]] | None = None

    async def load(self) -> None:
        try:
            obj = await self._store.async_load()
        except Exception:
            raise CatalogError("catalog load failed") from None
        if obj is None:
            self._records = []
            return
        if type(obj) is not dict or set(obj) != {"schema", "projects"} or obj["schema"] != SCHEMA:
            raise CatalogError("unknown catalog schema")
        data = obj["projects"]
        if type(data) is not list or len(data) > MAX_PROJECTS:
            raise CatalogError("invalid catalog size")
        rows = [sanitize_entry(r) for r in data]
        keys = [r["repository"].casefold() for r in rows]
        if len(set(keys)) != len(keys):
            raise CatalogError("duplicate catalog record")
        ids = [r["project_id"] for r in rows]
        if len(set(ids)) != len(ids):
            raise CatalogError("duplicate managed target identity")
        self._records = rows

    def list(self) -> list[dict[str, object]]:
        if self._records is None:
            raise CatalogError("catalog unavailable")
        return [dict(record) for record in self._records]

    async def _save(self, records: list[dict[str, object]]) -> None:
        if self._records is None:
            raise CatalogError("catalog unavailable")
        if len(records) > MAX_PROJECTS:
            raise CatalogError("catalog full")
        if (len({r["project_id"] for r in records}) != len(records)
            or len({r["repository"].casefold() for r in records}) != len(records)):
            raise CatalogError("duplicate managed target identity")
        try:
            await self._store.async_save({"schema": SCHEMA, "projects": records})
        except Exception:
            raise CatalogError("catalog save failed") from None
        self._records = records

    async def add(self, repository: str, name: str) -> dict[str, object]:
        candidate = proposal(repository, name, origin="manual")
        async with self._lock:
            rows = self.list()
            if any(x["repository"].casefold() == candidate["repository"].casefold() for x in rows):
                raise CatalogError("project already recorded")
            await self._save(rows + [candidate])
            return dict(candidate)

    async def import_v1(self, config_entries: object) -> dict[str, int]:
        proposals = v1_proposals(config_entries)
        async with self._lock:
            rows = self.list()
            have = {x["repository"].casefold() for x in rows}
            fresh = [x for x in proposals if x["repository"].casefold() not in have]
            if fresh:
                await self._save(rows + fresh)
            return {"added": len(fresh), "already_present": len(proposals)-len(fresh)}

    async def set_retention(self, repository: str, retention: int) -> dict[str, object]:
        value = normalize_repo(repository)
        if type(retention) is not int or not MIN_RETENTION <= retention <= MAX_RETENTION:
            raise CatalogError("invalid retention")
        async with self._lock:
            rows = self.list()
            found = next((i for i, x in enumerate(rows)
                          if x["repository"].casefold() == value.casefold()), None)
            if found is None:
                raise CatalogError("project not found")
            rows[found] = sanitize_entry({**rows[found], "backup_retention": retention})
            await self._save(rows)
            return dict(rows[found])
