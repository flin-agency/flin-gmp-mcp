# macOS installation (Claude Desktop)

1. Download [flin-gmp-mcp.mcpb](https://github.com/flin-agency/flin-gmp-mcp/releases/latest/download/flin-gmp-mcp.mcpb) from the latest release. Versioned packages remain available.
2. Open the file with a current Claude Desktop version that supports uv-based
   desktop extensions. Alternatively import it from Claude's extension settings.
3. Enter the Google Cloud **Desktop app** OAuth client ID and client secret supplied by your administrator or password manager.
4. Keep all four products enabled or choose a comma-separated subset of
   `admin,dv360,cm360,sa360`. Enable those APIs and grant product access in Google.
5. Run `connection_status`, then `authenticate`, and complete sign-in in your browser.
6. Test the enabled product using the small discovery read listed in the README.

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
uv run python scripts/build_mcpb.py --tag v0.1.6
uv run python scripts/check_mcpb.py dist/mcpb/flin-gmp-mcp-0.1.6.mcpb
```

The builder validates the manifest against the official MCPB v0.4 schema, includes only
allowlisted runtime files, rejects symlinks, checks version consistency and
creates a checksum. The smoke test starts the actual extracted bundle, discovers
all 33 tools and verifies the offline health check over MCP stdio.

## Server updates

**Automatic server updates** have been enabled by default since 0.1.5. At each
connector start, the new 0.1.6 launcher resolves the latest stable 0.1.x `flin-gmp-mcp` release in
`>= bundled version, <0.2` from PyPI using a package-cache refresh. Restart Claude Desktop or the connector to load a new server; compatible
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

You can explicitly disable automatic updates to pin the bundled server.
The 0.1.6 starter accepts only stable 0.1.x versions at or above its bundled version.
This boundary preserves Python 3.12, `flin_gmp_mcp.server.main`, stdio, the current
OAuth environment variables/scopes, private JSON token layout and existing tool
interfaces. Tests reject downgrades, pre-releases and 0.2/1.x versions. Future minor
or major interfaces must be assessed and may need a new starter. Older 0.1.4/0.1.5
starters retain their historical `<1` bound; importing the new bundle once applies
the narrower bound and the new fallback diagnostics.

With the new starter, `connection_status` and `health_check` report:

| Field | Meaning |
| --- | --- |
| `server_version` | Server code actually running; `health_check.version` remains |
| `extension_version` | Installed starter version, independent of PyPI updates |
| `runtime_source` | `pypi`, `cache`, `bundled`, or `unknown` for old/direct launchers |
| `update_status` | `updated`, `cached_fallback`, `bundled_fallback`, `disabled`, or `unknown` |
| `fallback_active` | `true` for a cache/bundled fallback, `false` otherwise, `null` if unknown |

A cached fallback may happen to contain the current server; it still means the
online update attempt failed. Startup diagnostics go to stderr. Old starters lack
these markers: their running server version is still known, but fallback provenance
is explicitly unknown. A server update alone cannot replace an installed starter.

## Existing token permissions

Version 0.1.4 rejects token directories accessible by other users and token files
that are shared, symlinked, oversized or not owned by the current user. Files saved
by earlier versions already use the expected `0600`/`0700` permissions. If you
manually copied credentials or selected a shared directory, move them to dedicated
private storage and correct their permissions, or remove them and authenticate again.
Never paste token contents into a chat or issue.
