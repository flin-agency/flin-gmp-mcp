import json
import os
import stat
from unittest.mock import Mock

import pytest

from flin_gmp_mcp import auth
from flin_gmp_mcp.config import ConfigurationError, Settings, load_settings, resolve_token_path


@pytest.fixture
def settings(tmp_path):
    return Settings("client-id", "client-secret", tmp_path / "tokens", services=("admin",))


def token_info(settings):
    return {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "refresh_token": "never-expose-refresh",
        "token": "never-expose-access",
        "scopes": list(settings.scopes),
        "expiry": "2099-01-01T00:00:00Z",
        "token_uri": "https://oauth2.googleapis.com/token",
    }


def write_token(settings, info=None):
    settings.token_dir.mkdir(mode=0o700, exist_ok=True)
    settings.token_path.write_text(json.dumps(token_info(settings) if info is None else info))
    settings.token_path.chmod(0o600)


def test_defaults_and_selected_scopes(tmp_path):
    env = {
        "GOOGLE_CLIENT_ID": " id ",
        "GOOGLE_CLIENT_SECRET": " secret ",
        "GOOGLE_GMP_TOKEN_DIR": str(tmp_path),
        "GOOGLE_GMP_SERVICES": "admin,sa360,admin",
    }
    settings = load_settings(env)
    assert settings.services == ("admin", "sa360")
    assert len(settings.scopes) == 2
    assert settings.client_id == "id"
    assert "secret" not in repr(settings)


@pytest.mark.parametrize(
    "overrides",
    [
        {"GOOGLE_CLIENT_ID": " "},
        {"GOOGLE_GMP_SERVICES": "ads"},
        {"GOOGLE_GMP_SERVICES": ""},
        {"GOOGLE_GMP_OAUTH_PORT": "-1"},
        {"GOOGLE_GMP_OAUTH_PORT": "65536"},
        {"GOOGLE_GMP_OAUTH_PORT": "abc"},
        {"GOOGLE_GMP_TOKEN_DIR": "relative"},
        {"GOOGLE_GMP_QUOTA_PROJECT": "bad\nheader"},
    ],
)
def test_invalid_config(overrides):
    with pytest.raises(ConfigurationError):
        load_settings({"GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "secret", **overrides})


@pytest.mark.parametrize(
    "account", ["../outside", ".", "..", "/tmp/evil", "default", "Work", "", "a.b"]
)
def test_invalid_account(settings, account):
    with pytest.raises(ConfigurationError):
        resolve_token_path(settings=settings, account=account)


def test_named_accounts_are_separate(settings):
    assert resolve_token_path(settings=settings) != resolve_token_path(
        settings=settings, account="work"
    )
    assert resolve_token_path(settings=settings, account="work").name == "work.json"


def test_missing_token_never_opens_browser(settings, monkeypatch):
    flow = Mock()
    monkeypatch.setattr(auth, "_run_installed_app_flow", flow)
    with pytest.raises(auth.AuthenticationRequiredError):
        auth.get_credentials(settings=settings)
    flow.assert_not_called()
    assert auth.describe_auth_state(settings=settings)["status"] == "oauth_required"


def test_valid_token_status_does_not_refresh(settings, monkeypatch):
    write_token(settings)
    refresh = Mock()
    monkeypatch.setattr(auth, "_refresh_credentials", refresh)
    assert auth.get_credentials(settings=settings).token == "never-expose-access"
    status = auth.describe_auth_state(settings=settings)
    assert status == {"status": "ready", "has_token_file": True}
    assert "never-expose" not in json.dumps(status)
    refresh.assert_not_called()


@pytest.mark.parametrize("change", [{"client_id": "different"}, {"scopes": []}])
def test_reject_wrong_client_or_scopes(settings, change):
    write_token(settings, {**token_info(settings), **change})
    with pytest.raises(auth.AuthenticationRequiredError):
        auth.get_credentials(settings=settings)
    assert auth.describe_auth_state(settings=settings)["status"] == "oauth_required"


@pytest.mark.parametrize("bad", ["broken json", "[]", "null"])
def test_corrupt_token(settings, bad):
    settings.token_dir.mkdir(mode=0o700)
    settings.token_path.write_text(bad)
    settings.token_path.chmod(0o600)
    assert auth.describe_auth_state(settings=settings)["status"] == "invalid_token_file"
    with pytest.raises(auth.AuthenticationError):
        auth.get_credentials(settings=settings)


def test_expired_token_refreshes_and_persists(settings, monkeypatch):
    write_token(settings, {**token_info(settings), "expiry": "2000-01-01T00:00:00Z"})

    def refresh(credentials):
        credentials.token = "new-access-token"

    monkeypatch.setattr(auth, "_refresh_credentials", refresh)
    assert auth.get_credentials(settings=settings).token == "new-access-token"
    assert json.loads(settings.token_path.read_text())["token"] == "new-access-token"


def test_refresh_failure_requires_explicit_auth(settings, monkeypatch):
    write_token(settings, {**token_info(settings), "expiry": "2000-01-01T00:00:00Z"})
    monkeypatch.setattr(auth, "_refresh_credentials", Mock(side_effect=RuntimeError("secret")))
    flow = Mock()
    monkeypatch.setattr(auth, "_run_installed_app_flow", flow)
    with pytest.raises(auth.AuthenticationRequiredError):
        auth.get_credentials(settings=settings)
    flow.assert_not_called()


def test_failed_forced_login_preserves_existing_token(settings, monkeypatch):
    write_token(settings)
    before = settings.token_path.read_bytes()
    monkeypatch.setattr(auth, "_run_installed_app_flow", Mock(side_effect=TimeoutError()))
    with pytest.raises(TimeoutError):
        auth.get_credentials(settings=settings, interactive=True, force=True)
    assert settings.token_path.read_bytes() == before


def test_interactive_login_private_atomic_storage(settings, monkeypatch):
    creds = Mock()
    creds.to_json.return_value = json.dumps(token_info(settings))
    monkeypatch.setattr(auth, "_run_installed_app_flow", Mock(return_value=creds))
    auth.get_credentials(settings=settings, account="work", interactive=True)
    path = resolve_token_path(settings=settings, account="work")
    assert path.is_file()
    assert not settings.token_path.exists()
    assert list(settings.token_dir.iterdir()) == [path]
    if os.name != "nt":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(settings.token_dir.stat().st_mode) == 0o700


def test_refuse_symlink_token(settings, tmp_path):
    write_token(settings)
    other = tmp_path / "other"
    other.write_text("unchanged")
    settings.token_path.unlink()
    settings.token_path.symlink_to(other)
    with pytest.raises(auth.AuthenticationError):
        auth.save_credentials(Mock(to_json=lambda: "{}"), settings.token_path)
    assert other.read_text() == "unchanged"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions")
def test_refuse_world_writable_storage(settings):
    settings.token_dir.mkdir(mode=0o777)
    settings.token_dir.chmod(0o777)
    with pytest.raises(auth.AuthenticationError):
        auth.save_credentials(Mock(to_json=lambda: "{}"), settings.token_path)


def test_oauth_uses_pkce_loopback_timeout_and_no_stdout(settings, monkeypatch, capsys):
    import google_auth_oauthlib.flow

    credentials = Mock(scopes=settings.scopes, granted_scopes=settings.scopes)
    flow = Mock()
    flow.run_local_server.return_value = credentials
    factory = Mock(return_value=flow)
    monkeypatch.setattr(google_auth_oauthlib.flow.InstalledAppFlow, "from_client_config", factory)
    assert auth._run_installed_app_flow(settings) is credentials
    assert factory.call_args.kwargs["autogenerate_code_verifier"] is True
    options = flow.run_local_server.call_args.kwargs
    assert options["host"] == "127.0.0.1"
    assert options["timeout_seconds"] == 180
    assert options["authorization_prompt_message"] == ""
    assert capsys.readouterr().out == ""
    credentials.granted_scopes = ["unrelated"]
    with pytest.raises(auth.AuthenticationRequiredError):
        auth._run_installed_app_flow(settings)


def test_oauth_timeout_is_actionable_and_callback_codes_are_not_logged(
    settings, monkeypatch, caplog
):
    import logging

    import google_auth_oauthlib.flow

    def timeout(**kwargs):
        logging.getLogger("google_auth_oauthlib.flow").info("GET /?code=private-code HTTP/1.1")
        raise google_auth_oauthlib.flow.WSGITimeoutError("expired")

    flow = Mock()
    flow.run_local_server.side_effect = timeout
    monkeypatch.setattr(
        google_auth_oauthlib.flow.InstalledAppFlow, "from_client_config", Mock(return_value=flow)
    )
    with caplog.at_level(logging.INFO), pytest.raises(TimeoutError):
        auth._run_installed_app_flow(settings)
    assert "private-code" not in caplog.text
    assert not settings.token_path.exists()


def test_reject_symlinked_token_on_read(settings, tmp_path):
    write_token(settings)
    alias = resolve_token_path(settings=settings, account="work")
    alias.symlink_to(settings.token_path)
    with pytest.raises(auth.AuthenticationError, match="symlinked"):
        auth.get_credentials(settings=settings, account="work")


def test_malformed_scope_list_has_actionable_status(settings):
    write_token(settings, {**token_info(settings), "scopes": [{"bad": "scope"}]})
    assert auth.describe_auth_state(settings=settings)["status"] == "oauth_required"
    with pytest.raises(auth.AuthenticationRequiredError):
        auth.get_credentials(settings=settings)


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions")
@pytest.mark.parametrize("mode", [0o644, 0o660, 0o666])
def test_reject_shared_token_permissions_before_credentials(settings, monkeypatch, mode):
    write_token(settings)
    settings.token_path.chmod(mode)
    build = Mock()
    monkeypatch.setattr(auth, "_build_credentials_from_info", build)
    with pytest.raises(auth.AuthenticationError):
        auth.get_credentials(settings=settings)
    assert auth.describe_auth_state(settings=settings)["status"] == "invalid_token_file"
    build.assert_not_called()


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions")
@pytest.mark.parametrize("mode", [0o755, 0o770, 0o777])
def test_reject_shared_directory_on_read_and_write(settings, mode):
    write_token(settings)
    settings.token_dir.chmod(mode)
    with pytest.raises(auth.AuthenticationError):
        auth.get_credentials(settings=settings)
    with pytest.raises(auth.AuthenticationError):
        auth.save_credentials(Mock(to_json=lambda: "{}"), settings.token_path)
    assert stat.S_IMODE(settings.token_dir.stat().st_mode) == mode


def test_reject_symlinked_parent_directory_on_read(settings, tmp_path):
    write_token(settings)
    moved = tmp_path / "real-tokens"
    settings.token_dir.rename(moved)
    settings.token_dir.symlink_to(moved, target_is_directory=True)
    with pytest.raises(auth.AuthenticationError):
        auth.get_credentials(settings=settings)


@pytest.mark.skipif(os.name == "nt", reason="POSIX file descriptors")
def test_token_symlink_swap_cannot_redirect_read(settings, tmp_path, monkeypatch):
    write_token(settings)
    target = tmp_path / "outside.json"
    target.write_text(settings.token_path.read_text())
    target.chmod(0o600)
    real_open = os.open

    def swapped_open(path, flags, *args, **kwargs):
        if path == settings.token_path.name:
            settings.token_path.unlink()
            settings.token_path.symlink_to(target)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(auth.os, "open", swapped_open)
    with pytest.raises(auth.AuthenticationError):
        auth.get_credentials(settings=settings)


@pytest.mark.skipif(os.name == "nt", reason="POSIX special files")
@pytest.mark.parametrize("kind", ["fifo", "directory", "hardlink"])
def test_token_must_be_regular_unshared_file(settings, tmp_path, kind):
    write_token(settings)
    if kind == "hardlink":
        os.link(settings.token_path, tmp_path / "alias.json")
    else:
        settings.token_path.unlink()
        if kind == "fifo":
            os.mkfifo(settings.token_path, 0o600)
        else:
            settings.token_path.mkdir(mode=0o700)
    with pytest.raises(auth.AuthenticationError):
        auth.get_credentials(settings=settings)


@pytest.mark.parametrize("content", [b"x" * (auth.MAX_TOKEN_BYTES + 1), b"\xff"])
def test_oversized_or_non_text_tokens_are_rejected(settings, content):
    write_token(settings)
    settings.token_path.write_bytes(content)
    with pytest.raises(auth.AuthenticationError):
        auth.get_credentials(settings=settings)


@pytest.mark.skipif(os.name == "nt", reason="POSIX ownership")
def test_token_owned_by_different_user_is_rejected(settings, monkeypatch):
    write_token(settings)
    real_fstat = os.fstat

    def other_owner(fd):
        result = real_fstat(fd)
        if stat.S_ISREG(result.st_mode):
            values = list(result)
            values[4] = os.getuid() + 1
            return os.stat_result(values)
        return result

    monkeypatch.setattr(auth.os, "fstat", other_owner)
    with pytest.raises(auth.AuthenticationError):
        auth.get_credentials(settings=settings)
