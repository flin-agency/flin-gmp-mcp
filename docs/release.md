# Release checklist

Tag releases publish the Python package to PyPI and attach the macOS desktop
bundle and SHA-256 checksum to a GitHub release. Branch pushes only run CI.

1. Run all checks in `docs/testing.md` and live smoke tests with authorized accounts.
2. Keep the version in `pyproject.toml` and `src/flin_gmp_mcp/__init__.py`
   consistent; the HTTP User-Agent uses the latter. Update `uv.lock` using `uv lock` after version or
   dependency changes.
3. Configure a PyPI Trusted Publisher (pending publisher for a new project):
   - PyPI project: `flin-gmp-mcp`
   - GitHub owner: `flin-agency`
   - Repository: `flin-gmp-mcp`
   - Workflow: `release.yml`
   - Environment: `pypi`
4. Configure the GitHub `pypi` environment with the desired approval requirements.
5. Commit the release, create the matching `vX.Y.Z` tag and push it when ready.
   Only tag pushes trigger publishing. The workflow rejects a version mismatch,
   reruns tests and builds, validates Python metadata and the desktop bundle,
   then publishes using OIDC without a stored PyPI token.
6. Verify installation with `uvx flin-gmp-mcp@X.Y.Z` and the MCP handshake.

Do not tag a release until the package name and Trusted Publisher are configured.
