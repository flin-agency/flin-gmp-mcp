# Release checklist

The initial implementation is source-installable. Publishing to PyPI is a
separate release action; no package publication is implied by a GitHub push.

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
   reruns tests and builds, then publishes using OIDC without a stored PyPI token.
6. Verify installation with `uvx flin-gmp-mcp@X.Y.Z` and the MCP handshake.

Do not tag a release until the package name and Trusted Publisher are configured.
