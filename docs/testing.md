# Testing

## Local checks

```bash
uv sync --locked --extra dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
uv run twine check dist/*.whl dist/*.tar.gz
uv run python scripts/build_mcpb.py
uv run python scripts/check_mcpb.py dist/mcpb/flin-gmp-mcp.mcpb
```

The automated suite exercises configuration, isolated named accounts, OAuth
scope/client changes, token expiry and refresh, atomic private token storage,
campaign-protection/report-write allowlisting, pagination/filter mapping, date validation,
response-size bounds, sanitized errors, MCP annotations and input schemas.
A real stdio subprocess is initialized and queried without Google credentials.
Regression tests also hold Google requests open across repeated calls and verify
that health checks remain responsive, and that a timed-out request does not prevent
the next tool call from succeeding.
Request contracts are checked against a reduced snapshot of Google's public
Discovery documents retrieved on 2026-10-30 (CM360 creatives added from Discovery on 2026-10-31).

CI runs on Python 3.10, 3.12 and 3.14, plus a macOS bundle startup job.
The desktop builder uses Python and the official MCPB schema, avoiding Node build dependencies. Unit tests do not prove that a particular
Google account has product access or that its API quotas are available.

## Live smoke test (requires your own Google authorization)

1. Set Desktop OAuth credentials and enable the required Google APIs.
2. Start the MCP using the README's stdio client configuration.
3. Call `health_check`, then `authenticate`. Complete browser consent.
4. Discover each enabled product:
   - Admin: `list_organizations` → `get_organization` → `list_analytics_account_links`.
   - DV360: `list_dv360_partners` → `list_dv360_advertisers` → `list_dv360_campaigns`.
   - DV360 reports: `list_dv360_report_queries` → `list_dv360_reports` → `get_dv360_report`.
   - CM360: `list_cm360_profiles` → `list_cm360_advertisers` → `list_cm360_campaigns`.
   - CM360 reports: `list_cm360_reports` → `list_cm360_report_files` → `get_cm360_report_file`.
   - SA360: `list_sa360_customers` → `get_sa360_customer_clients` for a manager →
     `get_sa360_campaign_performance` for a client with a recent date range.
5. If a response includes `nextPageToken`, repeat with that `page_token` and all
   other arguments unchanged. Compare sample records and SA360 totals with the UI.
6. Restart the server and repeat a call to verify saved credentials work.
7. Optionally authenticate `account="work"` and verify default/named accounts
   remain separate. Never include tokens in screenshots, logs or issue reports.

No live authenticated API calls are part of the automated suite. Empty lists may
be legitimate. A 403 requires checking product membership, API enablement, scopes
and quota; it does not automatically mean the implementation is broken.

## CM360 creative smoke test

1. Discover a profile, advertiser and campaign, keeping the same account alias.
2. Call `list_cm360_creatives` with those IDs and a small page size. Follow
   `nextPageToken`; compare names, formats and sizes with the CM360 UI.
3. Call `get_cm360_creative` for an HTML5 result. Inspect `creativeAssets` for
   `BACKUP_IMAGE`, its identifier, filename and size. Also check an image creative
   and a creative without backup assets; absence must not produce invented URLs.
4. Record whether the actual response includes any usable backup-image URL.
   Filenames, click-through URLs and impression trackers do not count. The public
   v5 schema provides no backup-image download endpoint; metadata alone does not
   prove image availability. Do not fetch tracking URLs to test a thumbnail.
5. Confirm that missing previews are displayed as unavailable by the consuming UI.

This live check was not run during implementation: local Google OAuth client
configuration was unavailable. Automated fixtures cover metadata and absent assets,
not the ability to download a real backup image.

## Desktop updater

`tests/test_bootstrap.py` covers package-cache refreshes, environment isolation,
rejected downgrades/prereleases/major upgrades, timeouts, cached and bundled fallback,
stdout hygiene, default enabled updates and explicit disabling. The regular bundle
smoke test disables updates so pre-publication CI verifies the code being released.

After PyPI publication, the release workflow runs:

```bash
uv run python scripts/check_mcpb.py dist/mcpb/flin-gmp-mcp.mcpb --auto-update --preserve-settings --expected-version 0.1.6
```

It also downloads the original v0.1.4 `.mcpb` and performs the same update check
against it, expecting the new server version. The checker requires matching
`health_check.version` and `starting PyPI runtime` diagnostics, as well as the real
MCP handshake and tools. A working old/bundled fallback fails this check. Regression
tests cover those false-success cases. Publication uses bounded retries for PyPI
index propagation. The GitHub release is gated on both update checks.

An update takes effect when the connector restarts. No Google credentials or live
account access are needed for these checks.

## DV360 report writes and CSV reads

Automated tests verify report-only POST allowlisting, advertiser scoping, date
validation, non-idempotent write annotations, asynchronous execution parameters,
pending/failed states, CSV pagination, precise string values, download size bounds,
and rejection of arbitrary download hosts and redirects.

Live verification (not performed by the automated suite): create a STANDARD CSV
query for a test advertiser, run it, check status until DONE, and compare the CSV
records with DV360. Reuse that query for another date range and confirm that no
campaign settings change. Creation leaves a saved query in the Google account.

## Common status, compatibility and settings retention

`connection_status` checks only local configuration/token metadata; the unit tests
block browser, API and token-refresh helpers. Stored valid or refreshable tokens
report `auth_status=unknown`, never authenticated/live success. Existing health fields
remain and `server_version` is additive. Tests cover malformed configuration and
safe runtime/fallback diagnostics without credential or customer-data disclosure.

The current starter's compatibility range is stable 0.1.x at or above the bundled
version, not all pre-1.0 interfaces. Rejection tests include 0.2, 0.9, 1.x,
pre-releases and downgrades. Real bundle checks exercise Python 3.12, the existing
stdio entry point, OAuth environment fields, token layout and old tool discovery.

`--preserve-settings` uses synthetic OAuth configuration and a private synthetic
token. It starts the same extracted extension twice, checks the selected service,
local token state and running version, and requires unchanged token bytes. It never
opens a browser or contacts Google. The release workflow runs this against both
the new and original v0.1.4 bundles after PyPI publication. This tests launcher
settings/token preservation, not Claude's interactive settings UI.

Release checks distinguish Linux package tests, native Apple Silicon/macOS bundle
startup, Intel/macOS bundle startup, and live PyPI update checks. None is an actual
customer-account consent/API test; those remain the separately documented manual
procedure above. The builder checks both the stable alias and versioned package
are identical and includes both names in `SHA256SUMS`.
