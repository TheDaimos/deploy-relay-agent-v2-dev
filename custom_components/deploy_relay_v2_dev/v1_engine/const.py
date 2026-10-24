"""Minimal V1 engine compatibility contract scoped to DRA V2."""
from enum import StrEnum
from typing import Final

DEPLOY_DATA_DIR: Final = "deploy_relay_v2_dev"
APPROVED_LOGICAL_ROOT: Final = "/config"
MANIFEST_SCHEMA_V1: Final = "deploy-relay.deployment.v1"

class LifecycleAction(StrEnum):
    NONE = "none"
    FRONTEND_RELOAD = "frontend_reload"
    INTEGRATION_RELOAD = "integration_reload"
    HOME_ASSISTANT_RESTART = "home_assistant_restart"
