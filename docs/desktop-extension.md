# macOS installation (Claude Desktop)

1. Download `flin-gmp-mcp-0.1.1.mcpb` from the repository's v0.1.1 release.
2. Open the file with a current Claude Desktop version that supports uv-based
   desktop extensions. Alternatively import it from Claude's extension settings.
3. Enter your Google Cloud **Desktop app** OAuth client ID and client secret.
4. Keep all four products enabled or choose a comma-separated subset of
   `admin,dv360,cm360,sa360`. Enable those APIs and grant product access in Google.
5. Run `health_check`, then `authenticate`, and complete sign-in in your browser.

The bundle supports macOS and uses Python 3.12 through uv. It includes the server
source and dependency lockfile; the first launch needs internet access to obtain
runtime dependencies. It contains no credentials and does not require a local
Git checkout or a separately published PyPI package. It is an MCP extension,
not a macOS system `.pkg` installer. No administrator privileges are needed.

The bundle is unsigned. Its SHA-256 checksum accompanies the release.
Do not bypass any operating-system security interstitial; use Claude's supported
extension import flow. See the main README for OAuth setup and token storage.

## Rebuild and verify

```bash
uv sync --locked --extra dev
uv run python scripts/build_mcpb.py --tag v0.1.1
uv run python scripts/check_mcpb.py dist/mcpb/flin-gmp-mcp-0.1.1.mcpb
```

The builder validates the manifest against the official MCPB v0.4 schema, includes only
allowlisted runtime files, rejects symlinks, checks version consistency and
creates a checksum. The smoke test starts the actual extracted bundle, discovers
all 29 tools and verifies the offline health check over MCP stdio.
