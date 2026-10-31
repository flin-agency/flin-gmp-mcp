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
uv run python scripts/check_mcpb.py dist/mcpb/*.mcpb
```

The automated suite exercises configuration, isolated named accounts, OAuth
scope/client changes, token expiry and refresh, atomic private token storage,
read-only endpoint enforcement, pagination/filter mapping, date validation,
response-size bounds, sanitized errors, MCP annotations and input schemas.
A real stdio subprocess is initialized and queried without Google credentials.
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
