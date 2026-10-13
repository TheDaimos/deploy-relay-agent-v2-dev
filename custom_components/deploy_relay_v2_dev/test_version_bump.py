"""Narrow, opt-in test fixture increment. Not a generic GitHub writer."""
from __future__ import annotations

import asyncio
import base64
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


async def increase_test_version(session, token: str) -> dict:
    """GET exact fixed path, verify exact document, conditional PUT using blob SHA."""
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
                body = await response.content.read(4097)
                if len(body) > 4096:
                    raise TestVersionError("GitHub-Antwort zu groß")
        source = json.loads(body)
        if (type(source) is not dict or source.get("type") != "file" or
            source.get("path") != FILE_PATH or
            type(source.get("sha")) is not str or len(source["sha"]) != 40 or
            type(source.get("content")) is not str or
            source.get("encoding") != "base64" or
            source.get("size", 99999) > 2048):
            raise TestVersionError("Unerwartete GitHub-Dateiangaben")
        before, after, new_file = next_test_status(base64.b64decode(source["content"], validate=True))
        payload = {
            "message": f"test(dra-v2): advance isolated teststand to {after}",
            "content": base64.b64encode(new_file).decode("ascii"),
            "sha": source["sha"], "branch": "main",
        }
        async with asyncio.timeout(16):
            async with session.put(API_URL, headers=headers, json=payload,
                                   allow_redirects=False) as response:
                reply = await response.content.read(4097)
                if response.status == 409:
                    raise TestVersionError("Git-Konflikt: Datei inzwischen geändert")
                if response.status not in (200, 201) or len(reply) > 4096:
                    raise TestVersionError("GitHub hat die Teständerung nicht bestätigt")
        result = json.loads(reply)
        commit = result.get("commit") if isinstance(result, dict) else None
        sha = commit.get("sha") if isinstance(commit, dict) else None
        if type(sha) is not str or len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
            raise TestVersionError("GitHub-Commit konnte nicht bestätigt werden")
        return {"schema": "dra-v2-test-version.v1", "before": before,
                "after": after, "commit": sha, "repository": REPOSITORY}
    except TestVersionError:
        raise
    except (OSError, ValueError, UnicodeError, asyncio.TimeoutError):
        raise TestVersionError("GitHub-Teständerung fehlgeschlagen") from None
