# macOS installation (Claude Desktop)

1. Download `flin-gmp-mcp-0.1.5.mcpb` from the [v0.1.5 release](https://github.com/flin-agency/flin-gmp-mcp/releases/tag/v0.1.5).
2. Open the file with a current Claude Desktop version that supports uv-based
   desktop extensions. Alternatively import it from Claude's extension settings.
3. Enter your Google Cloud **Desktop app** OAuth client ID and client secret.
4. Keep all four products enabled or choose a comma-separated subset of
   `admin,dv360,cm360,sa360`. Enable those APIs and grant product access in Google.
5. Run `health_check`, then `authenticate`, and complete sign-in in your browser.

The bundle supports macOS and uses Python 3.12 through uv. It includes the reviewed server
source and dependency lockfile; the first launch needs internet access to obtain
runtime dependencies. It contains no credentials and does not require a local Git checkout. It is an MCP extension,
not a macOS system `.pkg` installer. No administrator privileges are needed.

The bundle is unsigned. Its SHA-256 checksum accompanies the release.
Do not bypass any operating-system security interstitial; use Claude's supported
extension import flow. See the main README for OAuth setup and token storage.

## Rebuild and verify

```bash
uv sync --locked --extra dev
uv run python scripts/build_mcpb.py --tag v0.1.5
uv run python scripts/check_mcpb.py dist/mcpb/flin-gmp-mcp-0.1.5.mcpb
```

The builder validates the manifest against the official MCPB v0.4 schema, includes only
allowlisted runtime files, rejects symlinks, checks version consistency and
creates a checksum. The smoke test starts the actual extracted bundle, discovers
all 32 tools and verifies the offline health check over MCP stdio.

## Server updates

**Automatic server updates** are enabled by default in version 0.1.5. At each
connector start, the launcher resolves the latest stable `flin-gmp-mcp` release in
`>= bundled version, <1` from PyPI using an explicit package upgrade and cache
refresh. Restart Claude Desktop or the connector to load a new server; compatible
server updates do not require reinstalling the extension.

If 0.1.4 is already installed, enable **Automatic server updates** once in the
extension settings. Saved settings can persist across bundle imports. The 0.1.4
launcher supports PyPI updates when enabled, so it can load the new server without
installing another bundle. Existing 0.1.2/0.1.3 bundles also support enabled updates.

Every tagged release publishes the server to PyPI and builds a new `.mcpb` for new
installations. The release workflow requires the new bundle and the baseline
0.1.4 bundle to start the exact new PyPI version before it publishes the GitHub
release. Version checks and launch diagnostics reject an old or bundled fallback.

The resolver receives only a limited set of operating-system settings; Google and
unrelated cloud credentials are not passed through its environment. This is
environment isolation, not a filesystem sandbox. Updates execute newer code and
dependencies; each release is tested and dependency-audited before publication.

An online check has a 30-second timeout, followed by an offline cache attempt with
the same limit, then the bundled fallback. A later restart retries the online
update. Diagnostics go to stderr; stdout is reserved for MCP. No updater runs
while Claude is closed. `health_check.version` always reports the running version,
even before Google credentials are configured. The displayed extension version
identifies the installed launcher, not necessarily the server it currently runs.

You can explicitly disable automatic updates to pin the bundled server. Major
version 1.x and changes to the launcher, manifest or permissions can still require
a new bundle; server updates within the supported 0.x line do not.

## Existing token permissions

Version 0.1.4 rejects token directories accessible by other users and token files
that are shared, symlinked, oversized or not owned by the current user. Files saved
by earlier versions already use the expected `0600`/`0700` permissions. If you
manually copied credentials or selected a shared directory, move them to dedicated
private storage and correct their permissions, or remove them and authenticate again.
Never paste token contents into a chat or issue.
