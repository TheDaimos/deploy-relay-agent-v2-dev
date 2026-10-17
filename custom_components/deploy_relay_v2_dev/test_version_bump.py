"""Narrow, opt-in test fixture increment. Not a generic GitHub writer."""
from __future__ import annotations

import asyncio
import base64
import binascii
import json

REPOSITORY = "TheDaimos/Test-Repo-DRA-V2"
FILE_PATH = "payload/teststatus.json"
API_URL = "https://api.github.com/repos/TheDaimos/Test-Repo-DRA-V2/contents/payload/teststatus.json"
ALLOWED_KEYS = frozenset({
    "schema", "teststand", "projekt", "installation", "erwarteter_zielordner",
    "home_assistant_neustart_erforderlich", "vertrauliche_daten",
})


class TestVersionError(ValueError):
    pass


def next_test_status(raw: bytes) -> tuple[int, int, bytes]:
    if not isinstance(raw, bytes) or len(raw) > 2048:
        raise TestVersionError("Ungültige Testdatei")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError):
        raise TestVersionError("Ungültiges Testdateiformat") from None
    if (type(data) is not dict or set(data) != ALLOWED_KEYS or
        data["schema"] != "dra-v2-safe-test.v1" or
        data["projekt"] != "Test-Repo-DRA-V2" or
        data["installation"] != "synthetische Testdaten" or
        data["erwarteter_zielordner"] != "/config/dra_v2_testprojekt" or
        data["home_assistant_neustart_erforderlich"] is not False or
        data["vertrauliche_daten"] is not False or
        type(data["teststand"]) is not int or not 1 <= data["teststand"] < 99999):
        raise TestVersionError("Unerwartete Testdatei; Änderung abgebrochen")
    before = data["teststand"]
    data["teststand"] = before + 1
    return before, before + 1, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


async def _read_bounded(response, maximum: int) -> bytes:
    """Read to EOF under a strict byte cap; aiohttp reads may be fragmented."""
    data = bytearray()
    while True:
        part = await response.content.read(min(2048, maximum + 1 - len(data)))
        if not part:
            return bytes(data)
        data.extend(part)
        if len(data) > maximum:
            raise TestVersionError("GitHub-Antwort zu groß")


async def increase_test_version(session, token: str, *, file_count: int = 1) -> dict:
    """GET exact fixed path, verify exact document, conditional PUT using blob SHA."""
    if type(file_count) is not int or not 1 <= file_count <= 7:
        raise TestVersionError("Nur 1 bis 7 isolierte Testdateien zulässig")
    if not isinstance(token, str) or not token or len(token) > 512:
        raise TestVersionError("Für das Test-Repository ist ein GitHub-Token erforderlich")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "DRA-V2-Isolated-Test-Version",
    }
    try:
        async with asyncio.timeout(16):
            async with session.get(API_URL, headers=headers, allow_redirects=False) as response:
                if response.status != 200:
                    raise TestVersionError("Testdatei konnte nicht gelesen werden")
                body = await _read_bounded(response, 4096)
        source = json.loads(body)
        if (type(source) is not dict or source.get("type") != "file" or
            source.get("path") != FILE_PATH or
            type(source.get("sha")) is not str or len(source["sha"]) != 40 or
            type(source.get("content")) is not str or
            source.get("encoding") != "base64" or
            type(source.get("size")) is not int or source["size"] > 2048):
            raise TestVersionError("Unerwartete GitHub-Dateiangaben")
        before, after, new_file = next_test_status(base64.b64decode("".join(source["content"].split()), validate=True))
        # Git's immutable tree/commit API changes all selected files atomically.
        # A concurrent branch movement rejects the ref update (never force push).
        api = "https://api.github.com/repos/TheDaimos/Test-Repo-DRA-V2"
        async def request(method, url, payload=None):
            async with asyncio.timeout(16):
                async with session.request(method, url, headers=headers, json=payload,
                                           allow_redirects=False) as response:
                    body = await _read_bounded(response, 65536)
                    if response.status < 200 or response.status >= 300:
                        raise TestVersionError("GitHub-Teständerung nicht bestätigt")
                    value = json.loads(body)
                    if type(value) is not dict:
                        raise TestVersionError("Ungültige GitHub-Antwort")
                    return value

        ref = await request("GET", api + "/git/ref/heads/main")
        old_commit = ref.get("object", {}).get("sha")
        if not isinstance(old_commit, str) or len(old_commit) != 40:
            raise TestVersionError("Git-Referenz ungültig")
        commit_info = await request("GET", api + "/git/commits/" + old_commit)
        base_tree = commit_info.get("tree", {}).get("sha")
        if not isinstance(base_tree, str) or len(base_tree) != 40:
            raise TestVersionError("Git-Baum ungültig")
        # Delete only fixtures already present; GitHub rejects absent paths.
        old_tree = await request("GET", api + "/git/trees/" + base_tree + "?recursive=1")
        entries = old_tree.get("tree")
        if old_tree.get("truncated") is True or not isinstance(entries, list):
            raise TestVersionError("Testprojekt-Dateibaum unvollständig")
        existing_paths = {item.get("path") for item in entries
                          if isinstance(item, dict) and item.get("type") == "blob"}
        # Exactly one required status file and up to six numbered fixtures.
        tree = [{"path": FILE_PATH, "mode": "100644", "type": "blob",
                 "content": new_file.decode("utf-8")}]
        for index in range(1, 7):
            path = f"payload/dra_test_{index:02d}.json"
            if index < file_count:
                body = {"schema": "dra-v2-fixture.v1", "teststand": after,
                        "datei": index + 1, "gesamt": file_count}
                tree.append({"path": path, "mode": "100644", "type": "blob",
                             "content": json.dumps(body, ensure_ascii=False) + "\n"})
            elif path in existing_paths:
                tree.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
        new_tree = await request("POST", api + "/git/trees",
                                 {"base_tree": base_tree, "tree": tree})
        tree_sha = new_tree.get("sha")
        if not isinstance(tree_sha, str) or len(tree_sha) != 40:
            raise TestVersionError("Testdateibaum nicht bestätigt")
        new_commit = await request("POST", api + "/git/commits", {
            "message": f"test(dra-v2): advance isolated {file_count}-file fixture to {after}",
            "tree": tree_sha, "parents": [old_commit],
        })
        sha = new_commit.get("sha")
        if not isinstance(sha, str) or len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
            raise TestVersionError("GitHub-Commit konnte nicht bestätigt werden")
        await request("PATCH", api + "/git/refs/heads/main",
                      {"sha": sha, "force": False})
        return {"schema": "dra-v2-test-version.v1", "before": before,
                "after": after, "commit": sha, "repository": REPOSITORY,
                "file_count": file_count}
    except TestVersionError:
        raise
    except (OSError, ValueError, UnicodeError, binascii.Error, TypeError, asyncio.TimeoutError):
        raise TestVersionError("GitHub-Teständerung fehlgeschlagen") from None
