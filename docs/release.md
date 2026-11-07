# Release checklist

Every server release must publish the Python package to PyPI **and** a newly built
macOS desktop bundle (versioned plus `flin-gmp-mcp.mcpb` alias) and SHA-256 checksums to GitHub. Automatic PyPI updates in the
extension stay enabled by default. Branch pushes only run CI; finish a release by
pushing the matching version tag.

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
   reruns tests and builds, audits locked runtime/development dependencies, validates Python
   metadata and the desktop bundle on both Apple Silicon and Intel macOS runners,
   then publishes using OIDC without a stored PyPI token.
6. After publishing to PyPI, the workflow verifies the exact new server version
   through both the current bundle and the baseline v0.1.4 bundle with updates
   enabled. Run `--preserve-settings` to check synthetic settings and token bytes
   over two starts. Cached/bundled fallbacks cannot pass this check. Allow bounded retries
   for PyPI index propagation. Only then publish the GitHub release.
7. Verify the public download and checksum. Report that ordinary server updates
   require a connector restart, not a new bundle installation. Version 0.1.4 users
   must enable automatic updates once; do not silently override an explicit opt-out.

Do not tag a release until the package name and Trusted Publisher are configured.
