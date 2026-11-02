# macOS installation (Claude Desktop)

1. Download `flin-gmp-mcp-0.1.2.mcpb` from the repository's v0.1.2 release.
2. Open the file with a current Claude Desktop version that supports uv-based
   desktop extensions. Alternatively import it from Claude's extension settings.
3. Enter your Google Cloud **Desktop app** OAuth client ID and client secret.
4. Keep all four products enabled or choose a comma-separated subset of
   `admin,dv360,cm360,sa360`. Enable those APIs and grant product access in Google.
5. Run `health_check`, then `authenticate`, and complete sign-in in your browser.

The bundle supports macOS and uses Python 3.12 through uv. It includes a fallback server
source and dependency lockfile; the first launch needs internet access to obtain
runtime dependencies. It contains no credentials and does not require a local Git checkout. It is an MCP extension,
not a macOS system `.pkg` installer. No administrator privileges are needed.

The bundle is unsigned. Its SHA-256 checksum accompanies the release.
Do not bypass any operating-system security interstitial; use Claude's supported
extension import flow. See the main README for OAuth setup and token storage.

## Rebuild and verify

```bash
uv sync --locked --extra dev
uv run python scripts/build_mcpb.py --tag v0.1.2
uv run python scripts/check_mcpb.py dist/mcpb/flin-gmp-mcp-0.1.2.mcpb
```

The builder validates the manifest against the official MCPB v0.4 schema, includes only
allowlisted runtime files, rejects symlinks, checks version consistency and
creates a checksum. The smoke test starts the actual extracted bundle, discovers
all 29 tools and verifies the offline health check over MCP stdio.

## Automatic server updates (from 0.1.2)

Install the 0.1.2 bundle once to replace the old fixed launcher. On each connector
start, the launcher checks PyPI for the latest stable `flin-gmp-mcp` version within
`>= bundled version, <1`. It prepares an isolated Python 3.12 runtime and starts it.
The extension declares dynamic tools, so the MCP runtime supplies the tool list.
The displayed extension version describes the launcher; `health_check.version`
identifies the server actually running.

Restart the connector or Claude Desktop to load a newly published server. A running
chat/server is not hot-swapped. If a chat retains its old tool list, start a new chat.
Google sign-in settings and saved tokens stay in their existing locations.

An online check has a 30-second timeout. On failure, the launcher tries the uv cache
(with another 30-second limit), then starts its bundled fallback. First installation
still requires internet for Python and the fallback's locked dependencies. Updates
must be published on PyPI; uploading a GitHub bundle alone does not update the server.
Major version 1.x and changes to launcher/configuration/scopes require a new bundle.

Turn off **Automatic server updates** in extension settings to use the bundled
version only (`FLIN_GMP_AUTO_UPDATE=false` for direct launcher testing). Update
resolution receives no Google environment variables. Diagnostics go to stderr;
stdout remains reserved for MCP. No background updater runs while Claude is closed.
