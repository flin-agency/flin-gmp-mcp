# macOS installation (Claude Desktop)

1. Download `flin-gmp-mcp-0.1.4.mcpb` from the [v0.1.4 release](https://github.com/flin-agency/flin-gmp-mcp/releases/tag/v0.1.4).
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
uv run python scripts/build_mcpb.py --tag v0.1.4
uv run python scripts/check_mcpb.py dist/mcpb/flin-gmp-mcp-0.1.4.mcpb
```

The builder validates the manifest against the official MCPB v0.4 schema, includes only
allowlisted runtime files, rejects symlinks, checks version consistency and
creates a checksum. The smoke test starts the actual extracted bundle, discovers
all 32 tools and verifies the offline health check over MCP stdio.

## Server updates

Version 0.1.4 disables automatic server updates by default. Install a newer GitHub
bundle to update the reviewed server and dependency lockfile together. Existing
installations can retain their previous settings: turn **Automatic server updates**
off explicitly after upgrading if it was previously enabled.

You can opt in to automatic updates in extension settings. At each connector start,
the launcher then resolves the latest stable `flin-gmp-mcp` release in
`>= bundled version, <1` from PyPI. This executes code and dependency versions that
are outside this bundle's security review. The resolver receives only a limited
set of operating-system settings; Google and unrelated cloud credentials are not
passed through its environment. This is environment isolation, not a filesystem
sandbox: any code you choose to execute has your user account's file access.

An online check has a 30-second timeout, followed by an offline cache attempt with
the same limit, then the bundled fallback. Diagnostics go to stderr; stdout is
reserved for MCP. No updater runs while Claude is closed. Updates take effect on
restart; `health_check.version` identifies the running server. Major version 1.x
and launcher/configuration/scope changes require installing a new bundle.

## Existing token permissions

Version 0.1.4 rejects token directories accessible by other users and token files
that are shared, symlinked, oversized or not owned by the current user. Files saved
by earlier versions already use the expected `0600`/`0700` permissions. If you
manually copied credentials or selected a shared directory, move them to dedicated
private storage and correct their permissions, or remove them and authenticate again.
Never paste token contents into a chat or issue.
