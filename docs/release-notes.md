## 0.1.6 — consistent desktop setup and connection status

Download **flin-gmp-mcp.mcpb** (stable name) or **flin-gmp-mcp-0.1.6.mcpb** below.
Both are identical and listed in **SHA256SUMS**. The extension ID is unchanged.
The README starts with Claude Desktop on Apple Silicon: download, install, enter
administrator/password-manager settings, Google sign-in and a product-specific read.
Intel support and developer installation remain available.

- New `connection_status`: running `server_version`, local configuration, cautious
  auth status, `live_access=not_checked` and a concrete next step. It makes no Google
  request, refreshes no token and opens no browser. A local token is not live proof.
- `health_check.version` remains; `server_version` and launcher diagnostics are additive.
- The new starter reports extension version, PyPI/cache/bundled source and fallback.
  Automatic updates remain enabled. The tested range is stable 0.1.x, not future
  0.2/1.x interfaces. Existing cache and bundled fallbacks remain available.
- Both new and original 0.1.4 bundles must start the new public PyPI server and retain
  synthetic saved settings/token bytes across two starts before GitHub publication.
- Short root privacy/security/support pages link detailed guidance. Token JSON is
  unencrypted private local storage; removing the extension alone may leave it behind.

**Existing installations:** compatible server updates deliver the new status tool
on restart. Import this package once for the new starter's visible fallback markers
and tighter compatibility bound. A 0.1.4 install needs automatic updates enabled
once. Normal later compatible server updates do not require another import.

Validation: 207 automated tests; lint/format, manifest/reproducible package and Python
metadata checks. Release gates require built-package startup outside the source tree
on Linux, Apple Silicon and Intel, plus live PyPI update/settings-retention checks.
These are not an interactive Claude installation or a real Google customer-account test.

DV360 report creation/execution saves resources at Google; campaigns, budgets and
targeting are unchanged. CM360 exposes metadata/existing report links; SA360 returns
performance rows directly. The package remains unsigned.
