from __future__ import annotations

import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

SCOPE_PREFIX = "https://www.googleapis.com/auth/"
SERVICE_SCOPES = {
    "admin": (SCOPE_PREFIX + "marketingplatformadmin.analytics.read",),
    "dv360": (SCOPE_PREFIX + "display-video", SCOPE_PREFIX + "doubleclickbidmanager"),
    "cm360": (SCOPE_PREFIX + "dfatrafficking", SCOPE_PREFIX + "dfareporting"),
    "sa360": (SCOPE_PREFIX + "doubleclicksearch",),
}
REQUIRED_ENV_VARS = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")


class ConfigurationError(RuntimeError):
    """Invalid or missing runtime configuration."""


def missing_required_env_vars(env: Mapping[str, str] | None = None) -> list[str]:
    source = os.environ if env is None else env
    return [name for name in REQUIRED_ENV_VARS if not source.get(name, "").strip()]


def default_token_dir(env: Mapping[str, str]) -> Path:
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    elif sys.platform.startswith("win"):
        root = Path(env.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        root = Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return root / "flin-gmp-mcp"


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str = field(repr=False)
    token_dir: Path
    services: tuple[str, ...] = tuple(SERVICE_SCOPES)
    oauth_port: int = 0
    quota_project: str | None = None

    @property
    def token_path(self) -> Path:
        return self.token_dir / "default.json"

    @property
    def scopes(self) -> tuple[str, ...]:
        return tuple(scope for service in self.services for scope in SERVICE_SCOPES[service])


def resolve_token_path(*, settings: Settings, account: str | None = None) -> Path:
    if account is None:
        return settings.token_path
    # Canonical lower-case names prevent aliases on case-insensitive filesystems.
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", account) or account == "default":
        raise ConfigurationError("Use a lower-case account name other than default.")
    return settings.token_dir / f"{account}.json"


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    source = os.environ if env is None else env
    if missing_required_env_vars(source):
        raise ConfigurationError("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    services = tuple(
        dict.fromkeys(
            item.strip()
            for item in source.get("GOOGLE_GMP_SERVICES", "admin,dv360,cm360,sa360").split(",")
        )
    )
    if not services or any(item not in SERVICE_SCOPES for item in services):
        raise ConfigurationError("GOOGLE_GMP_SERVICES must contain admin,dv360,cm360,sa360.")
    try:
        port = int(source.get("GOOGLE_GMP_OAUTH_PORT", "0"))
    except ValueError as exc:
        raise ConfigurationError("Invalid OAuth port.") from exc
    if not 0 <= port <= 65535:
        raise ConfigurationError("OAuth port must be between 0 and 65535.")
    token_dir = Path(source.get("GOOGLE_GMP_TOKEN_DIR") or default_token_dir(source)).expanduser()
    if not token_dir.is_absolute():
        raise ConfigurationError("GOOGLE_GMP_TOKEN_DIR must be absolute.")
    quota_project = source.get("GOOGLE_GMP_QUOTA_PROJECT", "").strip() or None
    if quota_project and not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", quota_project):
        raise ConfigurationError("Invalid quota project ID.")
    return Settings(
        client_id=source["GOOGLE_CLIENT_ID"].strip(),
        client_secret=source["GOOGLE_CLIENT_SECRET"].strip(),
        token_dir=token_dir,
        services=services,
        oauth_port=port,
        quota_project=quota_project,
    )
