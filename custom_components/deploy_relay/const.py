"""Constants for Deploy Relay."""

from enum import StrEnum
from typing import Final

DOMAIN: Final = "deploy_relay"
NAME: Final = "Deploy Relay Agent"
LEGACY_NAME: Final = "Deploy Relay"
VERSION: Final = "1.0.0"

CATALOG_SCHEMA_VERSION: Final = 1
MANIFEST_SCHEMA_V1: Final = "deploy-relay.deployment.v1"
DEPLOYMENT_CHANNEL_SCHEMA_V1: Final = "deploy-relay.channel.v1"
DEFAULT_MANIFEST_PATH: Final = "deploy-relay.json"
DEFAULT_CHANNEL_POLICY_PATH: Final = "deploy-relay-channel.json"
DEFAULT_CATALOG_REPOSITORY: Final = "TheDaimos/deploy-relay-agent-pub"
DEFAULT_CATALOG_PATH: Final = "registry/projects.json"
DEFAULT_CATALOG_REF: Final = "main"

DEPLOY_DATA_DIR: Final = "deploy_relay"
APPROVED_LOGICAL_ROOT: Final = "/config"

PANEL_URL_PATH: Final = "deploy-relay"
PANEL_STATIC_URL: Final = "/deploy_relay_static"
PANEL_ELEMENT: Final = "deploy-relay-panel"
PANEL_ICON: Final = "mdi:source-branch"

CONF_GITHUB_TOKEN: Final = "github_token"
CONF_DIAGNOSTIC_GIT_TOKEN: Final = "diagnostic_git_token"
DIAGNOSTIC_GIT_ROOT: Final = ".deploy-relay/diagnostics"
CONF_CLEAR_GITHUB_TOKEN: Final = "clear_github_token"
CONF_REPOSITORY: Final = "repository"
CONF_MANIFEST_PATH: Final = "manifest_path"
CONF_BACKUP_RETENTION: Final = "backup_retention"
CONF_SHOW_SIDEBAR_PANEL: Final = "show_sidebar_panel"
LEGACY_CONF_SHOW_SIDEBAR: Final = "show_sidebar"
DEFAULT_SHOW_SIDEBAR_PANEL: Final = True
DEFAULT_BACKUP_RETENTION: Final = 10
MIN_BACKUP_RETENTION: Final = 3
MAX_BACKUP_RETENTION: Final = 100

CONF_SOURCE_CHOICE: Final = "source_choice"
CONF_COMMIT_SHA: Final = "commit_sha"
CONF_SELECTED_SOURCE_KIND: Final = "selected_source_kind"
CONF_SELECTED_SOURCE_REF: Final = "selected_source_ref"
CONF_SELECTED_SOURCE_COMMIT: Final = "selected_source_commit"

SUBENTRY_TYPE_PROJECT: Final = "project"

# V0.15 permits active-target writes only after an explicit runtime DEVELOPMENT unlock.
PLATFORMS: Final = ()


class DeploymentMode(StrEnum):
    """Local write-permission mode."""

    LOCKED = "locked"
    DEVELOPMENT = "development"


class LifecycleAction(StrEnum):
    """Manifest-declared lifecycle requirement."""

    NONE = "none"
    FRONTEND_RELOAD = "frontend_reload"
    INTEGRATION_RELOAD = "integration_reload"
    HOME_ASSISTANT_RESTART = "home_assistant_restart"
