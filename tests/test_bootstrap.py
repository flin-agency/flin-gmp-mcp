import importlib.util
import json
import subprocess
from unittest.mock import Mock

import pytest

from scripts.build_mcpb import ROOT


@pytest.fixture
def bootstrap():
    spec = importlib.util.spec_from_file_location("desktop_bootstrap", ROOT / "mcpb/server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_refreshes_pypi_without_credentials(bootstrap, monkeypatch, tmp_path):
    python = tmp_path / "python"
    python.touch()
    run = Mock(return_value=Mock(stdout=json.dumps({"python": str(python), "version": "0.9.0"})))
    monkeypatch.setattr(bootstrap.subprocess, "run", run)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("UV_INDEX", "https://other.invalid")
    assert bootstrap.resolve_runtime("uv", offline=False) == (str(python), "0.9.0")
    command = run.call_args.args[0]
    assert "--refresh-package" in command
    assert "https://pypi.org/simple" in command
    assert f"flin-gmp-mcp>={bootstrap.__version__},<1" in command
    assert "GOOGLE_CLIENT_SECRET" not in run.call_args.kwargs["env"]
    assert "UV_INDEX" not in run.call_args.kwargs["env"]
    assert run.call_args.kwargs["timeout"] == 30


@pytest.mark.parametrize("version", ["0.0.1", "1.0.0", "0.2.0rc1", "not-a-version"])
def test_probe_rejects_downgrade_major_and_prerelease(bootstrap, monkeypatch, version):
    monkeypatch.setattr(
        bootstrap.subprocess,
        "run",
        Mock(return_value=Mock(stdout=json.dumps({"python": "/bin/sh", "version": version}))),
    )
    assert bootstrap.resolve_runtime("uv", offline=False) is None


@pytest.mark.parametrize("failure", [subprocess.TimeoutExpired("uv", 30), OSError(), ValueError()])
def test_probe_failures_are_recoverable(bootstrap, monkeypatch, failure):
    monkeypatch.setattr(bootstrap.subprocess, "run", Mock(side_effect=failure))
    assert bootstrap.resolve_runtime("uv", offline=False) is None


@pytest.mark.parametrize("cached", [True, False])
def test_network_failure_uses_cache_then_bundle(bootstrap, monkeypatch, cached, capsys):
    from flin_gmp_mcp import server

    monkeypatch.setenv("FLIN_GMP_AUTO_UPDATE", "true")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "preserved")
    monkeypatch.setattr(bootstrap.shutil, "which", lambda _: "/bin/uv")
    resolve = Mock(side_effect=[None, ("/cached/python", "0.9.0") if cached else None])
    monkeypatch.setattr(bootstrap, "resolve_runtime", resolve)
    execute = Mock(side_effect=SystemExit(0))
    monkeypatch.setattr(bootstrap.os, "execve", execute)
    fallback = Mock()
    monkeypatch.setattr(server, "main", fallback)
    if cached:
        with pytest.raises(SystemExit):
            bootstrap.main()
        assert execute.call_args.args[2]["GOOGLE_CLIENT_SECRET"] == "preserved"
        assert execute.call_args.args[1][1] == "-I"
        fallback.assert_not_called()
    else:
        bootstrap.main()
        fallback.assert_called_once()
    assert [c.kwargs["offline"] for c in resolve.call_args_list] == [False, True]
    assert capsys.readouterr().out == ""


def test_disabled_updates_use_bundle_without_network(bootstrap, monkeypatch):
    from flin_gmp_mcp import server

    monkeypatch.setenv("FLIN_GMP_AUTO_UPDATE", "false")
    resolve = Mock()
    monkeypatch.setattr(bootstrap, "resolve_runtime", resolve)
    fallback = Mock()
    monkeypatch.setattr(server, "main", fallback)
    bootstrap.main()
    resolve.assert_not_called()
    fallback.assert_called_once()
