"""Project-owned recommended deployment channel resolution."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from aiohttp import ClientSession

from .const import (
    DEFAULT_CHANNEL_POLICY_PATH,
    DEFAULT_MANIFEST_PATH,
    DEPLOYMENT_CHANNEL_SCHEMA_V1,
)
from .github_client import GitHubClient, GitHubNotFoundError
from .repository import normalize_repository
from .source_discovery import ResolvedSource, SourceKind, async_resolve_source

_PROJECT_ID = re.compile(r"^[a-z][a-z0-9_]*$")


class DeploymentChannelError(RuntimeError):
    """Recommended deployment channel cannot be established safely."""


@dataclass(frozen=True, slots=True)
class DeploymentChannelPolicy:
    """Project-owned recommendation metadata from the repository default branch."""

    project_id: str
    channel: str
    kind: SourceKind
    ref: str
    explicit: bool
    policy_ref: str
    policy_path: str


@dataclass(frozen=True, slots=True)
class RecommendedDeployment:
    """Resolved current recommendation bound to a canonical commit."""

    policy: DeploymentChannelPolicy
    resolved: ResolvedSource
    repository: str
    default_branch: str

    def matches(
        self,
        *,
        selected_kind: str | None,
        selected_ref: str | None,
        selected_commit: str | None,
    ) -> bool:
        return (
            selected_kind == self.resolved.kind.value
            and selected_ref == self.resolved.requested_ref
            and selected_commit == self.resolved.commit_sha
        )

    def as_dict(
        self,
        *,
        selected_kind: str | None = None,
        selected_ref: str | None = None,
        selected_commit: str | None = None,
    ) -> dict[str, Any]:
        selected_matches = self.matches(
            selected_kind=selected_kind,
            selected_ref=selected_ref,
            selected_commit=selected_commit,
        )
        same_moving_ref = (
            selected_kind == self.resolved.kind.value
            and selected_ref == self.resolved.requested_ref
            and bool(selected_commit)
            and selected_commit != self.resolved.commit_sha
        )
        if selected_matches and self.policy.explicit:
            status = "recommended_current"
        elif selected_matches:
            status = "fallback_current"
        elif same_moving_ref:
            status = "newer_recommended_available"
        elif selected_kind or selected_ref or selected_commit:
            status = "different_source_selected"
        else:
            status = "not_selected"

        return {
            "available": True,
            "explicit_policy": self.policy.explicit,
            "policy_path": self.policy.policy_path,
            "policy_ref": self.policy.policy_ref,
            "channel": self.policy.channel,
            "kind": self.resolved.kind.value,
            "ref": self.resolved.requested_ref,
            "commit_sha": self.resolved.commit_sha,
            "project_id": self.resolved.manifest.project_id,
            "project_name": self.resolved.manifest.project_name,
            "repository": self.repository,
            "default_branch": self.default_branch,
            "selected_matches": selected_matches,
            "safe_selected": bool(self.policy.explicit and selected_matches),
            "status": status,
        }


def parse_deployment_channel_policy(
    raw: str | bytes | dict[str, Any],
    *,
    expected_project_id: str,
    policy_ref: str,
    policy_path: str,
) -> DeploymentChannelPolicy:
    """Strictly parse one project-owned deployment channel policy."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as err:
            raise DeploymentChannelError(f"invalid channel JSON: {err.msg}") from err
    else:
        data = raw

    if not isinstance(data, dict):
        raise DeploymentChannelError("deployment channel policy must be an object")
    if data.get("schema") != DEPLOYMENT_CHANNEL_SCHEMA_V1:
        raise DeploymentChannelError("unsupported deployment channel schema")

    allowed_root = {"schema", "project_id", "recommended"}
    unknown_root = set(data) - allowed_root
    if unknown_root:
        raise DeploymentChannelError(
            f"deployment channel policy has unsupported fields: {sorted(unknown_root)!r}"
        )

    project_id = data.get("project_id")
    if not isinstance(project_id, str) or not _PROJECT_ID.fullmatch(project_id):
        raise DeploymentChannelError("deployment channel project_id is invalid")
    if project_id != expected_project_id:
        raise DeploymentChannelError(
            "deployment channel project_id does not match configured project"
        )

    recommended = data.get("recommended")
    if not isinstance(recommended, dict):
        raise DeploymentChannelError("recommended deployment must be an object")

    allowed_recommended = {"channel", "kind", "ref"}
    unknown_recommended = set(recommended) - allowed_recommended
    if unknown_recommended:
        raise DeploymentChannelError(
            "recommended deployment has unsupported fields"
        )

    channel = recommended.get("channel")
    kind = recommended.get("kind")
    ref = recommended.get("ref")
    if not isinstance(channel, str) or not channel.strip():
        raise DeploymentChannelError("recommended.channel must be non-empty")
    if not isinstance(ref, str) or not ref.strip():
        raise DeploymentChannelError("recommended.ref must be non-empty")
    try:
        source_kind = SourceKind(kind)
    except (TypeError, ValueError) as err:
        raise DeploymentChannelError("recommended.kind is unsupported") from err

    return DeploymentChannelPolicy(
        project_id=project_id,
        channel=channel.strip(),
        kind=source_kind,
        ref=ref.strip(),
        explicit=True,
        policy_ref=policy_ref,
        policy_path=policy_path,
    )


async def async_resolve_recommended_deployment(
    session: ClientSession,
    repository: str,
    *,
    expected_project_id: str,
    token: str | None = None,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    policy_path: str = DEFAULT_CHANNEL_POLICY_PATH,
) -> RecommendedDeployment:
    """Resolve the authoritative current deployment recommendation.

    The policy is always read from the repository default branch. If no explicit
    policy exists, the default branch is used as a clearly marked fallback.
    """
    normalized = normalize_repository(repository)
    client = GitHubClient(session, token)
    info = await client.async_get_repository(normalized)

    try:
        raw_policy = await client.async_get_text_file(
            info.full_name,
            policy_path,
            ref=info.default_branch,
        )
    except GitHubNotFoundError:
        policy = DeploymentChannelPolicy(
            project_id=expected_project_id,
            channel="default",
            kind=SourceKind.BRANCH,
            ref=info.default_branch,
            explicit=False,
            policy_ref=info.default_branch,
            policy_path=policy_path,
        )
    else:
        policy = parse_deployment_channel_policy(
            raw_policy,
            expected_project_id=expected_project_id,
            policy_ref=info.default_branch,
            policy_path=policy_path,
        )

    try:
        resolved = await async_resolve_source(
            session,
            info.full_name,
            kind=policy.kind,
            ref=policy.ref,
            token=token,
            manifest_path=manifest_path,
            expected_project_id=expected_project_id,
        )
    except Exception as err:
        raise DeploymentChannelError(
            f"recommended deployment {policy.kind.value}:{policy.ref} is invalid"
        ) from err

    return RecommendedDeployment(
        policy=policy,
        resolved=resolved,
        repository=info.full_name,
        default_branch=info.default_branch,
    )


def unavailable_recommendation(
    err: Exception,
) -> dict[str, Any]:
    """Return a secret-free unavailable recommendation payload."""
    return {
        "available": False,
        "error_type": type(err).__name__,
        "reason": str(err),
    }
