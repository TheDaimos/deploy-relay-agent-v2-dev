"""Config flow, project import, source selection and fallback read-only preview."""

from __future__ import annotations

import json
import logging
from functools import partial
from pathlib import Path
from typing import Any, override

import probatio

from homeassistant.config_entries import (
    SOURCE_USER,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlowWithReload,
    FlowType,
    SubentryFlowContext,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_BACKUP_RETENTION,
    CONF_CLEAR_GITHUB_TOKEN,
    CONF_COMMIT_SHA,
    CONF_DIAGNOSTIC_GIT_TOKEN,
    CONF_GITHUB_TOKEN,
    CONF_MANIFEST_PATH,
    CONF_REPOSITORY,
    CONF_SHOW_SIDEBAR_PANEL,
    CONF_SELECTED_SOURCE_COMMIT,
    CONF_SELECTED_SOURCE_KIND,
    CONF_SELECTED_SOURCE_REF,
    CONF_SOURCE_CHOICE,
    DEFAULT_BACKUP_RETENTION,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_SHOW_SIDEBAR_PANEL,
    LEGACY_CONF_SHOW_SIDEBAR,
    DOMAIN,
    NAME,
    SUBENTRY_TYPE_PROJECT,
)
from .github_client import (
    GitHubAccessError,
    GitHubApiError,
    GitHubAuthenticationError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from .path_policy import PathPolicyError
from .preview import PreviewError, PreviewOperation, build_preview
from .project_import import ProjectImportError, async_probe_project
from .repository import RepositoryIdentityError
from .source_discovery import (
    SourceDiscoveryError,
    SourceKind,
    SourceManifestNotFound,
    async_discover_sources,
    async_load_frozen_manifest,
    async_resolve_source,
)
from .source_inventory import SourceInventoryError, async_build_source_inventory

_LOGGER = logging.getLogger(__name__)

_MANUAL_COMMIT = "__manual_commit__"
_EMPTY_SCHEMA = probatio.Schema({})

_TOKEN_SELECTOR = TextSelector(
    TextSelectorConfig(
        type=TextSelectorType.PASSWORD,
        autocomplete="off",
    )
)

_PROJECT_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_REPOSITORY): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
                autocomplete="off",
            )
        ),
        probatio.Optional(
            CONF_MANIFEST_PATH,
            default=DEFAULT_MANIFEST_PATH,
        ): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
                autocomplete="off",
            )
        ),
        probatio.Optional(CONF_GITHUB_TOKEN): _TOKEN_SELECTOR,
    }
)

_PROJECT_RECONFIGURE_SCHEMA = _PROJECT_SCHEMA.extend(
    {
        probatio.Optional(
            CONF_CLEAR_GITHUB_TOKEN,
            default=False,
        ): BooleanSelector(),
    }
)

_COMMIT_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_COMMIT_SHA): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
                autocomplete="off",
            )
        )
    }
)


class DeployRelayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle Deploy Relay setup."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Return the Deploy Relay integration options flow."""
        del config_entry
        return DeployRelayOptionsFlow()

    @classmethod
    @callback
    @override
    def async_get_supported_subentry_types(
        cls,
        config_entry: ConfigEntry,
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return supported subentry types."""
        return {SUBENTRY_TYPE_PROJECT: ProjectSubentryFlowHandler}

    @override
    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Create the single Deploy Relay service entry."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})

        return self.async_show_form(
            step_id="user",
            data_schema=_EMPTY_SCHEMA,
        )

    @override
    async def async_on_create_entry(self, result: ConfigFlowResult) -> ConfigFlowResult:
        """Start the first project-import flow after initial setup."""
        subentry_result = await self.hass.config_entries.subentries.async_init(
            (result["result"].entry_id, SUBENTRY_TYPE_PROJECT),
            context=SubentryFlowContext(source=SOURCE_USER),
        )
        result["next_flow"] = (
            FlowType.CONFIG_SUBENTRIES_FLOW,
            subentry_result["flow_id"],
        )
        return result


class DeployRelayOptionsFlow(OptionsFlowWithReload):
    """Handle Deploy Relay integration options."""

    @override
    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Configure optional Deploy Relay UI integration behavior."""
        if user_input is not None:
            options = {
                **self.config_entry.options,
                CONF_SHOW_SIDEBAR_PANEL: bool(
                    user_input[CONF_SHOW_SIDEBAR_PANEL]
                ),
            }
            options.pop(LEGACY_CONF_SHOW_SIDEBAR, None)
            return self.async_create_entry(data=options)

        show_sidebar = bool(
            self.config_entry.options.get(
                CONF_SHOW_SIDEBAR_PANEL,
                DEFAULT_SHOW_SIDEBAR_PANEL,
            )
        )
        return self.async_show_form(
            step_id="init",
            data_schema=probatio.Schema(
                {
                    probatio.Required(
                        CONF_SHOW_SIDEBAR_PANEL,
                        default=show_sidebar,
                    ): BooleanSelector(),
                }
            ),
        )


class ProjectSubentryFlowHandler(ConfigSubentryFlow):
    """Import, reconfigure, select a source and preview one project."""

    def _current_project_token(self) -> str | None:
        """Return the current project's stored token."""
        subentry = self._get_reconfigure_subentry()
        token = subentry.data.get(CONF_GITHUB_TOKEN)
        return str(token).strip() if token else None

    def _project_context(self) -> tuple[str, str, str | None, str | None]:
        """Return repository, manifest path, trusted project id and token."""
        subentry = self._get_reconfigure_subentry()
        repository = str(subentry.data[CONF_REPOSITORY])
        manifest_path = str(
            subentry.data.get(CONF_MANIFEST_PATH, DEFAULT_MANIFEST_PATH)
        )
        project_id = (
            subentry.data.get("project_id")
            if subentry.data.get("status") == "ready"
            else None
        )
        token = subentry.data.get(CONF_GITHUB_TOKEN)
        return (
            repository,
            manifest_path,
            str(project_id) if project_id else None,
            str(token).strip() if token else None,
        )

    @staticmethod
    def _github_error_code(err: Exception) -> str:
        """Map GitHub exceptions to stable UI errors."""
        if isinstance(err, GitHubAuthenticationError):
            return "invalid_auth"
        if isinstance(err, GitHubRateLimitError):
            return "rate_limited"
        if isinstance(err, GitHubAccessError):
            return "access_denied"
        if isinstance(err, GitHubNotFoundError):
            return "source_not_found"
        if isinstance(err, GitHubApiError):
            return "cannot_connect"
        return "unknown"

    async def _async_probe(
        self,
        user_input: dict[str, Any],
        *,
        reconfigure: bool,
    ):
        """Probe one repository without exposing its credential."""
        supplied_token = str(user_input.get(CONF_GITHUB_TOKEN, "")).strip()
        clear_token = bool(user_input.get(CONF_CLEAR_GITHUB_TOKEN, False))
        stored_token = self._current_project_token() if reconfigure else None

        if clear_token:
            token = None
        else:
            token = supplied_token or stored_token

        result = await async_probe_project(
            async_get_clientsession(self.hass),
            str(user_input[CONF_REPOSITORY]),
            token=token,
            manifest_path=str(
                user_input.get(CONF_MANIFEST_PATH, DEFAULT_MANIFEST_PATH)
            ),
        )
        return result, token

    def _duplicate_exists(
        self,
        repository_unique_id: str,
        *,
        ignore_subentry_id: str | None = None,
    ) -> bool:
        """Return whether another imported project already uses this repository."""
        entry = self._get_entry()
        for subentry in entry.subentries.values():
            if subentry.subentry_type != SUBENTRY_TYPE_PROJECT:
                continue
            if ignore_subentry_id and subentry.subentry_id == ignore_subentry_id:
                continue
            if subentry.unique_id == repository_unique_id:
                return True
        return False

    async def _async_process_project(
        self,
        user_input: dict[str, Any],
        *,
        reconfigure: bool,
        step_id: str,
    ) -> SubentryFlowResult:
        """Validate input and create or update a project subentry."""
        errors: dict[str, str] = {}

        try:
            result, token = await self._async_probe(
                user_input,
                reconfigure=reconfigure,
            )
        except RepositoryIdentityError:
            errors["base"] = "invalid_repository"
        except PathPolicyError:
            errors["base"] = "invalid_manifest_path"
        except GitHubAuthenticationError:
            errors["base"] = "invalid_auth"
        except GitHubRateLimitError:
            errors["base"] = "rate_limited"
        except GitHubAccessError:
            errors["base"] = "access_denied"
        except GitHubNotFoundError:
            errors["base"] = "repository_not_found"
        except ProjectImportError:
            errors["base"] = "invalid_manifest"
        except GitHubApiError:
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected Deploy Relay project import error")
            errors["base"] = "unknown"
        else:
            unique_id = result.repository.casefold()
            current = self._get_reconfigure_subentry() if reconfigure else None
            if self._duplicate_exists(
                unique_id,
                ignore_subentry_id=current.subentry_id if current else None,
            ):
                errors["base"] = "already_imported"
            else:
                persistent_data = result.as_subentry_data()
                if token:
                    persistent_data[CONF_GITHUB_TOKEN] = token

                if reconfigure:
                    assert current is not None
                    persistent_data[CONF_BACKUP_RETENTION] = current.data.get(
                        CONF_BACKUP_RETENTION,
                        DEFAULT_BACKUP_RETENTION,
                    )
                    diagnostic_git_token = current.data.get(
                        CONF_DIAGNOSTIC_GIT_TOKEN
                    )
                    if diagnostic_git_token:
                        persistent_data[CONF_DIAGNOSTIC_GIT_TOKEN] = (
                            diagnostic_git_token
                        )

                if reconfigure:
                    assert current is not None
                    return self.async_update_and_abort(
                        self._get_entry(),
                        current,
                        title=result.project_name,
                        data=persistent_data,
                        unique_id=unique_id,
                    )

                return self.async_create_entry(
                    title=result.project_name,
                    data=persistent_data,
                    unique_id=unique_id,
                )

        suggested = {
            CONF_REPOSITORY: user_input.get(CONF_REPOSITORY, ""),
            CONF_MANIFEST_PATH: user_input.get(
                CONF_MANIFEST_PATH,
                DEFAULT_MANIFEST_PATH,
            ),
            CONF_CLEAR_GITHUB_TOKEN: user_input.get(
                CONF_CLEAR_GITHUB_TOKEN,
                False,
            ),
        }
        schema = _PROJECT_RECONFIGURE_SCHEMA if reconfigure else _PROJECT_SCHEMA
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(
                schema,
                suggested,
            ),
            errors=errors,
        )

    async def _async_resolve_and_store_source(
        self,
        kind: SourceKind,
        ref: str,
    ) -> SubentryFlowResult:
        """Resolve a source to immutable commit identity and store metadata."""
        repository, manifest_path, project_id, token = self._project_context()

        try:
            resolved = await async_resolve_source(
                async_get_clientsession(self.hass),
                repository,
                kind=kind,
                ref=ref,
                token=token,
                manifest_path=manifest_path,
                expected_project_id=project_id,
            )
        except SourceManifestNotFound:
            return self.async_abort(reason="source_manifest_missing")
        except SourceDiscoveryError:
            return self.async_abort(reason="invalid_source")
        except (
            GitHubAuthenticationError,
            GitHubRateLimitError,
            GitHubAccessError,
            GitHubNotFoundError,
            GitHubApiError,
        ) as err:
            return self.async_abort(reason=self._github_error_code(err))
        except Exception:
            _LOGGER.exception("Unexpected Deploy Relay source resolution error")
            return self.async_abort(reason="unknown")

        return self.async_update_and_abort(
            self._get_entry(),
            self._get_reconfigure_subentry(),
            title=resolved.manifest.project_name,
            data_updates={
                "project_id": resolved.manifest.project_id,
                "project_name": resolved.manifest.project_name,
                "status": "ready",
                CONF_SELECTED_SOURCE_KIND: resolved.kind.value,
                CONF_SELECTED_SOURCE_REF: resolved.requested_ref,
                CONF_SELECTED_SOURCE_COMMIT: resolved.commit_sha,
            },
        )

    @override
    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> SubentryFlowResult:
        """Import a project from GitHub."""
        if user_input is not None:
            return await self._async_process_project(
                user_input,
                reconfigure=False,
                step_id="user",
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_PROJECT_SCHEMA,
        )

    @override
    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> SubentryFlowResult:
        """Choose which part of an imported project to reconfigure."""
        del user_input
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=["repository_settings", "source_selection", "preview"],
        )

    async def async_step_repository_settings(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> SubentryFlowResult:
        """Re-probe or change repository/manifest/credential settings."""
        if user_input is not None:
            return await self._async_process_project(
                user_input,
                reconfigure=True,
                step_id="repository_settings",
            )

        subentry = self._get_reconfigure_subentry()
        return self.async_show_form(
            step_id="repository_settings",
            data_schema=self.add_suggested_values_to_schema(
                _PROJECT_RECONFIGURE_SCHEMA,
                {
                    CONF_REPOSITORY: subentry.data[CONF_REPOSITORY],
                    CONF_MANIFEST_PATH: subentry.data.get(
                        CONF_MANIFEST_PATH,
                        DEFAULT_MANIFEST_PATH,
                    ),
                    CONF_CLEAR_GITHUB_TOKEN: False,
                },
            ),
        )

    async def async_step_source_selection(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> SubentryFlowResult:
        """Discover and select a branch, tag, release or manual commit."""
        if user_input is not None:
            choice = str(user_input[CONF_SOURCE_CHOICE])
            if choice == _MANUAL_COMMIT:
                return await self.async_step_manual_commit()

            try:
                decoded = json.loads(choice)
                kind = SourceKind(decoded["kind"])
                ref = str(decoded["ref"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                return self.async_abort(reason="invalid_source")

            return await self._async_resolve_and_store_source(kind, ref)

        repository, _, _, token = self._project_context()
        errors: dict[str, str] = {}
        options: list[SelectOptionDict] = []

        try:
            discovered = await async_discover_sources(
                async_get_clientsession(self.hass),
                repository,
                token=token,
            )
        except (
            GitHubAuthenticationError,
            GitHubRateLimitError,
            GitHubAccessError,
            GitHubNotFoundError,
            GitHubApiError,
        ) as err:
            errors["base"] = self._github_error_code(err)
        except Exception:
            _LOGGER.exception("Unexpected Deploy Relay source discovery error")
            errors["base"] = "unknown"
        else:
            options.extend(
                SelectOptionDict(
                    value=json.dumps(
                        {"kind": item.kind.value, "ref": item.ref},
                        separators=(",", ":"),
                    ),
                    label=item.label,
                )
                for item in discovered.candidates
            )

        options.append(
            SelectOptionDict(
                value=_MANUAL_COMMIT,
                label="Commit SHA",
            )
        )

        subentry = self._get_reconfigure_subentry()
        selected_kind = subentry.data.get(CONF_SELECTED_SOURCE_KIND)
        selected_ref = subentry.data.get(CONF_SELECTED_SOURCE_REF)
        default_value: str | None = None
        if selected_kind and selected_ref:
            default_value = json.dumps(
                {"kind": selected_kind, "ref": selected_ref},
                separators=(",", ":"),
            )
            if not any(option["value"] == default_value for option in options):
                default_value = None

        key = (
            probatio.Required(CONF_SOURCE_CHOICE, default=default_value)
            if default_value
            else probatio.Required(CONF_SOURCE_CHOICE)
        )

        return self.async_show_form(
            step_id="source_selection",
            data_schema=probatio.Schema(
                {
                    key: SelectSelector(
                        SelectSelectorConfig(options=options)
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_manual_commit(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> SubentryFlowResult:
        """Select an explicit commit SHA."""
        if user_input is not None:
            return await self._async_resolve_and_store_source(
                SourceKind.COMMIT,
                str(user_input[CONF_COMMIT_SHA]),
            )

        return self.async_show_form(
            step_id="manual_commit",
            data_schema=_COMMIT_SCHEMA,
        )

    async def async_step_preview(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> SubentryFlowResult:
        """Build and display a fresh read-only preview."""
        if user_input is not None:
            return self.async_abort(reason="preview_complete")

        subentry = self._get_reconfigure_subentry()
        commit = subentry.data.get(CONF_SELECTED_SOURCE_COMMIT)
        selected_ref = subentry.data.get(CONF_SELECTED_SOURCE_REF)
        selected_kind = subentry.data.get(CONF_SELECTED_SOURCE_KIND)

        if not commit or not selected_ref or not selected_kind:
            return self.async_abort(reason="source_not_selected")

        repository, manifest_path, project_id, token = self._project_context()
        session = async_get_clientsession(self.hass)
        resource_lock = self._get_entry().runtime_data.resource_lock
        await resource_lock.acquire()

        try:
            manifest = await async_load_frozen_manifest(
                session,
                repository,
                commit_sha=str(commit),
                token=token,
                manifest_path=manifest_path,
                expected_project_id=project_id,
            )
            inventory = await async_build_source_inventory(
                session,
                manifest,
                source_ref=str(selected_ref),
                source_commit=str(commit),
                token=token,
            )
            result = await self.hass.async_add_executor_job(
                partial(
                    build_preview,
                    manifest,
                    inventory,
                    config_root=Path(self.hass.config.config_dir),
                )
            )
        except SourceManifestNotFound:
            return self.async_abort(reason="source_manifest_missing")
        except (
            SourceDiscoveryError,
            SourceInventoryError,
            PreviewError,
            ValueError,
        ):
            _LOGGER.exception("Deploy Relay preview validation failed")
            return self.async_abort(reason="preview_failed")
        except (
            GitHubAuthenticationError,
            GitHubRateLimitError,
            GitHubAccessError,
            GitHubNotFoundError,
            GitHubApiError,
        ) as err:
            return self.async_abort(reason=self._github_error_code(err))
        except Exception:
            _LOGGER.exception("Unexpected Deploy Relay preview error")
            return self.async_abort(reason="unknown")
        finally:
            resource_lock.release()

        shown = []
        counts = {
            PreviewOperation.ADD: 0,
            PreviewOperation.CHANGE: 0,
            PreviewOperation.REMOVE: 0,
            PreviewOperation.UNCHANGED: 0,
        }
        for item in result.files:
            counts[item.operation] += 1
            if (
                item.operation is not PreviewOperation.UNCHANGED
                and len(shown) < 40
            ):
                shown.append(item)

        symbols = {
            PreviewOperation.ADD: "＋",
            PreviewOperation.CHANGE: "~",
            PreviewOperation.REMOVE: "−",
            PreviewOperation.UNCHANGED: "=",
        }
        details = "\n".join(
            f"{symbols[item.operation]} {item.target_path}"
            for item in shown
        )
        affected = (
            counts[PreviewOperation.ADD]
            + counts[PreviewOperation.CHANGE]
            + counts[PreviewOperation.REMOVE]
        )
        if affected > len(shown):
            details = (
                f"{details}\n… +{affected - len(shown)} weitere"
                if details
                else f"… +{affected - len(shown)} weitere"
            )
        if not details:
            details = "="

        summary = (
            f"＋ {counts[PreviewOperation.ADD]} · "
            f"~ {counts[PreviewOperation.CHANGE]} · "
            f"− {counts[PreviewOperation.REMOVE]} · "
            f"= {counts[PreviewOperation.UNCHANGED]}"
        )
        source = (
            f"{selected_kind} · {selected_ref} · "
            f"{str(commit)[:12]}"
        )

        return self.async_show_form(
            step_id="preview",
            data_schema=_EMPTY_SCHEMA,
            description_placeholders={
                "source": source,
                "summary": summary,
                "details": details,
            },
        )
