## Security release 0.1.4 — Claude Desktop for macOS

Download **flin-gmp-mcp-0.1.4.mcpb** below and import it in Claude Desktop's extension
settings. The same package supports Apple Silicon and Intel Macs. Enter your own
Google Desktop OAuth client ID/secret, enable the Google products you use, then run
`health_check` and `authenticate`. First launch needs internet for Python/dependencies.

- Updated OAuthLib and pytest to versions without the known advisories found by
  the dependency scan; future releases now require a passing dependency audit.
- Hardened token reads against shared permissions, incorrect ownership, symlink
  swaps, hard links, special files and oversized input.
- Automatic server updates are **off by default**, so the package starts its
  included server with locked dependencies. Existing settings may persist: disable
  **Automatic server updates** explicitly if it was enabled before upgrading.
- Update probes no longer inherit unrelated cloud secrets from the environment.
- GitHub publication uses pinned Actions and requires bundle startup checks on
  both Apple Silicon and Intel macOS runners.

All 32 tools remain available, including DV360 report creation and CSV reads.
Campaign settings cannot be changed. Google OAuth scopes can still grant broader
permissions; enable only products you need.

Validation: 186 tests, lint/format, Python package and reproducible MCPB checks,
real MCP startup and dependency/secret scans. See **SECURITY-REVIEW.md** and
**dependency-audit.json** below for scope, findings and limits.

The bundle is unsigned and includes **SHA256SUMS**. Interactive Claude Desktop
installation and live authenticated Google product behavior have not been tested.
