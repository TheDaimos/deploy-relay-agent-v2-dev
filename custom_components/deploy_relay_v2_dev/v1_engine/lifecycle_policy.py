"""Effective post-install lifecycle classification.

This module keeps the v1 manifest backwards compatible while allowing DRA to
safely downgrade a manifest-declared full Home Assistant restart when the
actual preview proves that every changed file is a frontend-only resource.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from .const import LifecycleAction
from .manifest import DeploymentManifest
from .preview import PreviewOperation, PreviewResult

_FRONTEND_EXTENSIONS = frozenset(
    {
        ".js",
        ".mjs",
        ".cjs",
        ".css",
        ".html",
        ".htm",
        ".svg",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".ico",
        ".avif",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".map",
    }
)


@dataclass(frozen=True, slots=True)
class LifecycleAssessment:
    """Declared and effective lifecycle action for one exact preview."""

    declared: LifecycleAction
    effective: LifecycleAction
    reason: str
    changed_files: int
    frontend_only: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "declared": self.declared.value,
            "effective": self.effective.value,
            "reason": self.reason,
            "changed_files": self.changed_files,
            "frontend_only": self.frontend_only,
        }


def is_safe_frontend_target(target_path: str) -> bool:
    """Return True only for unambiguous static frontend targets.

    Path classification is intentionally conservative. A frontend-looking file
    extension outside a dedicated frontend root is not enough to downgrade a
    restart requirement.
    """

    path = PurePosixPath(target_path)
    parts = path.parts
    suffix = path.suffix.casefold()
    if suffix not in _FRONTEND_EXTENSIONS:
        return False

    if len(parts) >= 4 and parts[0] == "custom_components" and parts[2] == "frontend":
        return True

    if len(parts) >= 2 and parts[0] == "www":
        return True

    return False


def lifecycle_for_target_paths(target_paths: list[str] | tuple[str, ...]) -> LifecycleAction:
    """Return the conservative post-write lifecycle for exact target paths.

    This is used by backup restoration, which has no source manifest preview but
    still knows every target path it actually changed.
    """

    paths = tuple(target_paths)
    if not paths:
        return LifecycleAction.NONE
    if all(is_safe_frontend_target(path) for path in paths):
        return LifecycleAction.FRONTEND_RELOAD
    return LifecycleAction.HOME_ASSISTANT_RESTART


def assess_lifecycle(
    manifest: DeploymentManifest,
    preview: PreviewResult,
) -> LifecycleAssessment:
    """Derive the effective post-install action from the exact preview.

    V1 compatibility rule:
    - no actual changes -> NONE;
    - an explicit manifest action other than HOME_ASSISTANT_RESTART remains
      authoritative;
    - HOME_ASSISTANT_RESTART may be downgraded to FRONTEND_RELOAD only when
      every changed file is proven to be a safe frontend target;
    - mixed/backend/unknown changes remain a full restart.
    """

    changed = tuple(
        item
        for item in preview.files
        if item.operation is not PreviewOperation.UNCHANGED
    )
    if not changed:
        return LifecycleAssessment(
            declared=manifest.after_install,
            effective=LifecycleAction.NONE,
            reason="no_changes",
            changed_files=0,
            frontend_only=False,
        )

    if manifest.after_install is not LifecycleAction.HOME_ASSISTANT_RESTART:
        return LifecycleAssessment(
            declared=manifest.after_install,
            effective=manifest.after_install,
            reason="declared_lifecycle",
            changed_files=len(changed),
            frontend_only=False,
        )

    frontend_only = all(is_safe_frontend_target(item.target_path) for item in changed)
    if frontend_only:
        return LifecycleAssessment(
            declared=manifest.after_install,
            effective=LifecycleAction.FRONTEND_RELOAD,
            reason="frontend_only_downgrade",
            changed_files=len(changed),
            frontend_only=True,
        )

    return LifecycleAssessment(
        declared=manifest.after_install,
        effective=LifecycleAction.HOME_ASSISTANT_RESTART,
        reason="backend_or_unknown_changes",
        changed_files=len(changed),
        frontend_only=False,
    )
