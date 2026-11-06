"""Desktop bootstrap: audited bundle by default, with explicitly opt-in PyPI updates."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from flin_gmp_mcp import __version__

PACKAGE = "flin-gmp-mcp"
UPDATE_TIMEOUT = 30
# Only OS/runtime settings are needed to resolve packages. Do not pass unrelated
# cloud credentials, proxy credentials or package-index configuration to the probe.
UPDATE_ENV_KEYS = {
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "TMPDIR",
    "TMP",
    "TEMP",
    "SYSTEMROOT",
    "WINDIR",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "XDG_CACHE_HOME",
    "XDG_DATA_HOME",
    "LANG",
    "LC_ALL",
}
PROBE = (
    "import json,sys; from flin_gmp_mcp import __version__; "
    "from flin_gmp_mcp.server import main; "
    "print(json.dumps({'python':sys.executable,'version':__version__}))"
)


def runtime_command(uv: str, *, offline: bool) -> list[str]:
    return [
        uv,
        "tool",
        "run",
        "--isolated",
        "--no-config",
        "--python",
        "3.12",
        "--default-index",
        "https://pypi.org/simple",
        "--prerelease",
        "disallow",
        "--from",
        f"{PACKAGE}>={__version__},<1",
        *(["--offline"] if offline else ["--refresh-package", PACKAGE]),
        "python",
        "-I",
        "-c",
        PROBE,
    ]


def resolve_runtime(uv: str, *, offline: bool) -> tuple[str, str] | None:
    # Package resolution does not need Google credentials or inherited index settings.
    env = {key: value for key, value in os.environ.items() if key in UPDATE_ENV_KEYS}
    try:
        completed = subprocess.run(
            runtime_command(uv, offline=offline),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=UPDATE_TIMEOUT,
            check=True,
        )
        data = json.loads(completed.stdout)
        version, executable = data["version"], data["python"]
        if not re.fullmatch(r"0\.\d+\.\d+", version):
            return None
        if tuple(map(int, version.split("."))) < tuple(map(int, __version__.split("."))):
            return None
        if not Path(executable).is_absolute() or not Path(executable).is_file():
            return None
        return executable, version
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return None


def main() -> None:
    uv = shutil.which("uv")
    if os.environ.get("FLIN_GMP_AUTO_UPDATE", "false").lower() == "true" and uv:
        for offline in (False, True):
            runtime = resolve_runtime(uv, offline=offline)
            if runtime is None:
                continue
            executable, version = runtime
            print(f"flin-gmp-mcp: starting PyPI runtime {version}", file=sys.stderr)
            try:
                os.execve(
                    executable,
                    [executable, "-I", "-c", "from flin_gmp_mcp.server import main; main()"],
                    dict(os.environ),
                )
            except OSError:
                continue
    print(f"flin-gmp-mcp: starting bundled runtime {__version__}", file=sys.stderr)
    from flin_gmp_mcp.server import main as bundled_main

    bundled_main()


if __name__ == "__main__":
    main()
