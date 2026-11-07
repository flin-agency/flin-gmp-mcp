import json
from unittest.mock import Mock

import pytest

from flin_gmp_mcp import __version__, auth, server


@pytest.fixture(autouse=True)
def isolated_status(monkeypatch, tmp_path):
    for key in (
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_GMP_SERVICES",
        "FLIN_GMP_EXTENSION_VERSION",
        "FLIN_GMP_RUNTIME_SOURCE",
        "FLIN_GMP_UPDATE_STATUS",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GOOGLE_GMP_TOKEN_DIR", str(tmp_path / "tokens"))
    for module, name in (
        (server, "request"),
        (server, "get_credentials"),
        (auth, "_refresh_credentials"),
        (auth, "_run_installed_app_flow"),
    ):
        monkeypatch.setattr(module, name, Mock(side_effect=AssertionError("Must stay local")))


def test_incomplete_and_legacy_diagnostics():
    value = server.connection_status()
    assert value["server_version"] == __version__
    assert value["configuration_status"] == "incomplete"
    assert value["auth_status"] == "unknown"
    assert value["live_access"] == "not_checked"
    assert value["extension_version"] is None
    assert value["fallback_active"] is None
    assert server.health_check()["version"] == server.health_check()["server_version"]


@pytest.mark.parametrize(
    "state,expected",
    [
        ("ready", "unknown"),
        ("refreshable", "unknown"),
        ("invalid_token_file", "unknown"),
        ("oauth_required", "unauthenticated"),
    ],
)
def test_local_tokens_never_prove_live_authentication(monkeypatch, state, expected):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "private-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "private-secret")
    monkeypatch.setattr(
        server,
        "describe_auth_state",
        Mock(
            return_value={
                "status": state,
                "has_token_file": True,
                "error": "private-exception",
            }
        ),
    )
    value = server.connection_status()
    assert value["configuration_status"] == "configured"
    assert value["auth_status"] == expected
    assert value["live_access"] == "not_checked"
    assert "private-" not in json.dumps(value)


def test_missing_token_and_invalid_configuration(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    assert server.connection_status()["auth_status"] == "unauthenticated"
    monkeypatch.setenv("GOOGLE_GMP_SERVICES", "invalid")
    assert server.connection_status()["configuration_status"] == "incomplete"


@pytest.mark.parametrize(
    "source,update,fallback",
    [
        ("pypi", "updated", False),
        ("cache", "cached_fallback", True),
        ("bundled", "bundled_fallback", True),
        ("bundled", "disabled", False),
    ],
)
def test_runtime_provenance_is_visible(monkeypatch, source, update, fallback):
    monkeypatch.setenv("FLIN_GMP_EXTENSION_VERSION", "0.1.6")
    monkeypatch.setenv("FLIN_GMP_RUNTIME_SOURCE", source)
    monkeypatch.setenv("FLIN_GMP_UPDATE_STATUS", update)
    value = server.connection_status()
    assert value["extension_version"] == "0.1.6"
    assert value["runtime_source"] == source
    assert value["fallback_active"] is fallback
    assert server.health_check()["update_status"] == update


def test_diagnostics_do_not_echo_arbitrary_environment(monkeypatch):
    for key in ("FLIN_GMP_EXTENSION_VERSION", "FLIN_GMP_RUNTIME_SOURCE", "FLIN_GMP_UPDATE_STATUS"):
        monkeypatch.setenv(key, "private-data")
    assert "private-data" not in json.dumps(server.connection_status())
