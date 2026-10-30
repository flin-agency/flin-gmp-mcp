from __future__ import annotations

import json
import logging
import os
import stat
import tempfile
from functools import partial
from pathlib import Path
from typing import Any

from .config import Settings, load_settings, resolve_token_path


class AuthenticationError(RuntimeError):
    """Raised when credential loading or refresh fails."""


class AuthenticationRequiredError(AuthenticationError):
    """Raised when interactive OAuth is required to continue."""


def _load_token_info(token_path: Path) -> dict[str, Any]:
    try:
        info = json.loads(token_path.read_text(encoding="utf-8"))
        if not isinstance(info, dict):
            raise AuthenticationError("Token file must contain an object.")
        return info
    except FileNotFoundError as exc:
        raise AuthenticationRequiredError("No token file found.") from exc
    except json.JSONDecodeError as exc:
        raise AuthenticationError("Token file is not valid JSON.") from exc


def _build_credentials_from_info(info: dict[str, Any], scopes: tuple[str, ...]) -> Any:
    try:
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise AuthenticationError(
            "Google auth dependencies are not installed. Install project dependencies first."
        ) from exc

    try:
        return Credentials.from_authorized_user_info(info, scopes=scopes)
    except Exception as exc:
        raise AuthenticationError("Failed to load credentials from token data.") from exc


def _refresh_credentials(credentials: Any) -> None:
    try:
        from google.auth.transport.requests import Request
    except ImportError as exc:
        raise AuthenticationError(
            "Google auth transport dependency is not installed. Install project dependencies first."
        ) from exc

    credentials.refresh(partial(Request(), timeout=30))


def _run_installed_app_flow(settings: Settings) -> Any:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow, WSGITimeoutError
    except ImportError as exc:
        raise AuthenticationError(
            "google-auth-oauthlib is not installed. Install project dependencies first."
        ) from exc

    client_config = {
        "installed": {
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(
        client_config, settings.scopes, autogenerate_code_verifier=True
    )
    # The library logs the callback URL (including its authorization code) at INFO.
    logging.getLogger("google_auth_oauthlib.flow").setLevel(logging.WARNING)
    try:
        credentials = flow.run_local_server(
            host="127.0.0.1",
            port=settings.oauth_port,
            timeout_seconds=180,
            open_browser=True,
            access_type="offline",
            prompt="consent select_account",
            authorization_prompt_message="",
            success_message=(
                "Google Marketing Platform authorization complete. You can close this tab and return to your MCP client."
            ),
        )
    except WSGITimeoutError as exc:
        raise TimeoutError("Browser sign-in timed out.") from exc

    granted = credentials.granted_scopes or credentials.scopes or []
    if not set(settings.scopes).issubset(granted):
        raise AuthenticationRequiredError("Required permissions were not granted. Sign in again.")
    return credentials


def _ensure_private_token_dir(token_path: Path) -> None:
    token_dir = token_path.parent
    if token_dir.is_symlink():
        raise AuthenticationError("Refusing to store credentials in a symlinked directory.")

    try:
        token_dir.mkdir(mode=0o700, parents=True)
    except FileExistsError:
        pass

    directory_stat = token_dir.lstat()
    if not stat.S_ISDIR(directory_stat.st_mode):
        raise AuthenticationError("Token storage must be a regular directory.")
    if os.name != "nt":
        # Never chmod a caller-provided existing directory. It may be shared
        # with other applications; only newly created storage is private by default.
        if directory_stat.st_uid != os.getuid() or directory_stat.st_mode & 0o022:
            raise AuthenticationError(
                "Token storage must be owned by the current user and must not "
                "be writable by other users. Choose a dedicated private directory."
            )


def _write_credentials_atomically(token_json: str, token_path: Path) -> None:
    if token_path.is_symlink():
        raise AuthenticationError("Refusing to write credentials through a symlinked token path.")

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{token_path.name}.",
        dir=token_path.parent,
    )
    tmp_path = Path(tmp_name)
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)

        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(token_json)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(tmp_path, token_path)
        if os.name != "nt":
            os.chmod(token_path, 0o600)
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def save_credentials(credentials: Any, token_path: Path) -> None:
    _ensure_private_token_dir(token_path)
    _write_credentials_atomically(credentials.to_json(), token_path)


def get_credentials(
    *,
    settings: Settings | None = None,
    account: str | None = None,
    interactive: bool = False,
    force: bool = False,
) -> Any:
    resolved_settings = settings or load_settings()
    token_path = resolve_token_path(settings=resolved_settings, account=account)

    try:
        if force:
            raise AuthenticationRequiredError("New sign-in requested.")
        info = _load_token_info(token_path)
        _validate_token_info(info, resolved_settings)
    except AuthenticationRequiredError:
        if not interactive:
            raise
        credentials = _run_installed_app_flow(resolved_settings)
        save_credentials(credentials, token_path)
        return credentials

    credentials = _build_credentials_from_info(info, resolved_settings.scopes)

    if getattr(credentials, "valid", False):
        return credentials

    if getattr(credentials, "expired", False) and getattr(credentials, "refresh_token", None):
        try:
            _refresh_credentials(credentials)
        except Exception as exc:
            if not interactive:
                raise AuthenticationRequiredError(
                    "Stored credentials could not be refreshed and interactive OAuth is required."
                ) from exc
            credentials = _run_installed_app_flow(resolved_settings)

        save_credentials(credentials, token_path)
        return credentials

    if not interactive:
        raise AuthenticationRequiredError(
            "Interactive OAuth is required to obtain Google Marketing Platform credentials."
        )

    credentials = _run_installed_app_flow(resolved_settings)
    save_credentials(credentials, token_path)
    return credentials


def describe_auth_state(
    *,
    settings: Settings | None = None,
    account: str | None = None,
) -> dict[str, Any]:
    resolved_settings = settings or load_settings()
    token_path = resolve_token_path(settings=resolved_settings, account=account)

    if not token_path.exists():
        return {
            "status": "oauth_required",
            "has_token_file": False,
        }

    try:
        info = _load_token_info(token_path)
        _validate_token_info(info, resolved_settings)
        credentials = _build_credentials_from_info(info, resolved_settings.scopes)
    except AuthenticationRequiredError:
        return {"status": "oauth_required", "has_token_file": True}
    except AuthenticationError as exc:
        return {
            "status": "invalid_token_file",
            "has_token_file": True,
            "error": str(exc),
        }

    if getattr(credentials, "valid", False):
        status = "ready"
    elif getattr(credentials, "expired", False) and getattr(credentials, "refresh_token", None):
        status = "refreshable"
    else:
        status = "oauth_required"

    return {
        "status": status,
        "has_token_file": True,
    }


def _validate_token_info(info: dict[str, Any], settings: Settings) -> None:
    if info.get("client_id") != settings.client_id:
        raise AuthenticationRequiredError("Token belongs to a different OAuth client.")
    scopes = info.get("scopes", [])
    if not isinstance(scopes, list) or not set(settings.scopes).issubset(scopes):
        raise AuthenticationRequiredError("Sign in again to grant the configured scopes.")
