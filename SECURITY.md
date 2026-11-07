# Security

The server runs locally over stdio. Google login uses a temporary loopback callback
with PKCE/state. Google API routes are allowlisted. Campaigns, budgets and targeting
cannot be changed; DV360 report creation and execution are explicit write tools.
Google scopes can permit broader operations than the server exposes.

OAuth access/refresh tokens are **unencrypted local JSON**, protected by private
POSIX ownership/permissions (`0700` directories, `0600` files), atomic writes and
symlink checks. The secret setting is marked sensitive for Claude's protected
settings storage; this does not encrypt the separate token files. See [privacy
and removal](PRIVACY.md). Status tools return no credentials or customer data.

PyPI updates stay enabled by default. The new starter accepts stable 0.1.x releases
and keeps cached/bundled fallbacks visible in status. No update replaces a running
session. The environment allowlist is not an OS sandbox: executable packages have
the user's filesystem access. Python/uv, PyPI, Google and the MCP client remain
trust dependencies. Packages are unsigned; SHA-256 checks detect changed bytes.

Release gates validate the manifest, audit dependencies, run tests, start the built
bundle outside the source tree on Linux, Apple Silicon and Intel, then verify the
public PyPI version through new and baseline bundles with synthetic saved settings.
These checks are not an interactive Claude installation or a real customer-account
OAuth/API test. `connection_status` is local and never claims live access.

[Detailed historical 0.1.5 security review](docs/security-review-0.1.5.md) ·
[Current test procedure](docs/testing.md) · [Update compatibility](docs/desktop-extension.md#server-updates)

Report suspected vulnerabilities privately to **flin@flin.agency** with version and
reproduction steps. Never send tokens, secrets or customer report data.
