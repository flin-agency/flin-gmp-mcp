"""Smoke-test a locally built bundle with its locked Python runtime and real MCP stdio."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def validate_runtime(
    health: dict,
    diagnostics: str,
    *,
    auto_update: bool,
    expected_version: str | None,
) -> str:
    version = health.get("version")
    if not isinstance(version, str) or not version:
        raise RuntimeError("Running server did not report its version")
    if expected_version is not None and version != expected_version:
        raise RuntimeError(f"Expected server {expected_version}, got {version}")
    if (
        auto_update
        and f"flin-gmp-mcp: starting PyPI runtime {version}" not in diagnostics.splitlines()
    ):
        raise RuntimeError("PyPI update did not start; a bundled fallback is not an update")
    return version


async def check_bundle(
    bundle: Path, *, auto_update: bool = False, expected_version: str | None = None
) -> None:
    with (
        tempfile.TemporaryDirectory(prefix="flin-gmp smoke ") as directory,
        tempfile.TemporaryFile(mode="w+", encoding="utf-8") as diagnostics,
    ):
        root = Path(directory)
        with zipfile.ZipFile(bundle) as archive:
            for name in archive.namelist():
                if Path(name).is_absolute() or ".." in Path(name).parts:
                    raise ValueError("Unsafe archive path")
            archive.extractall(root)
        manifest = json.loads((root / "manifest.json").read_text())
        env = {key: value for key, value in os.environ.items() if not key.startswith("GOOGLE_")}
        env["FLIN_GMP_AUTO_UPDATE"] = str(auto_update).lower()
        config = manifest["server"]["mcp_config"]
        params = StdioServerParameters(
            command=config["command"],
            args=[arg.replace("${__dirname}", str(root)) for arg in config["args"]],
            env=env,
        )
        async with stdio_client(params, errlog=diagnostics) as (read, write):
            async with ClientSession(
                read, write, read_timeout_seconds=timedelta(seconds=120)
            ) as session:
                await session.initialize()
                listing = await session.list_tools()
                expected = {t["name"] for t in manifest["tools"]}
                actual = {t.name for t in listing.tools}
                if (not auto_update and actual != expected) or (
                    auto_update and not expected <= actual
                ):
                    raise RuntimeError("Bundle manifest and discovered tools differ")
                result = await session.call_tool("health_check", {})
                if result.isError or result.structuredContent["status"] != "missing_configuration":
                    raise RuntimeError("Bundle health check failed")
        diagnostics.seek(0)
        version = validate_runtime(
            result.structuredContent,
            diagnostics.read(),
            auto_update=auto_update,
            expected_version=expected_version or (None if auto_update else manifest["version"]),
        )
        source = "PyPI" if auto_update else "bundled"
        print(f"Bundle startup and tools passed: {bundle.name}; {source} server {version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--auto-update", action="store_true", help="Exercise the PyPI update path")
    parser.add_argument("--expected-version", help="Require this exact running server version")
    args = parser.parse_args()
    asyncio.run(
        check_bundle(
            args.bundle, auto_update=args.auto_update, expected_version=args.expected_version
        )
    )
