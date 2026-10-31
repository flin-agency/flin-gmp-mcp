# flin-gmp-mcp

Read-only MCP server for **Google Marketing Platform**, built like the other
[flin MCPs](https://github.com/flin-agency): Python, FastMCP, `uv`, browser OAuth,
private local tokens, and stdio transport.

## Supported products

| Product | Tools and data | API |
| --- | --- | --- |
| GMP Admin | Organizations and linked Analytics accounts | v1alpha |
| Display & Video 360 | Partners, advertisers, campaigns, insertion orders, line items, creatives | v4 |
| DV360 reporting | Existing report queries, report runs, status and download URLs | Bid Manager v2 |
| Campaign Manager 360 | User profiles, advertisers, campaigns, creatives with sizes/assets, saved reports and existing file metadata/URLs | v5 |
| Search Ads 360 | Customer discovery, manager hierarchy, campaign performance, custom SELECT queries and field discovery | Reporting v0 |

GA4 reporting belongs in the separate `flin-ga4-mcp`. Google Ads, Search Console
and Google Tag Manager are outside this package's scope. GMP account links are
**Analytics account links**, not a universal cross-product account directory.

No campaign mutations, account linking, report creation/execution, or arbitrary
HTTP requests are exposed. DV360 and CM360 report tools return existing metadata
and URLs, not downloaded CSV contents. SA360 returns performance rows directly.
DV360 uses v4; v5 was still labelled beta in Google's documentation when this
implementation was verified on 2026-10-30.

## Quickstart from this repository

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --extra dev
```

Create a Google Cloud project and enable the APIs you will use:

- Google Marketing Platform Admin API (`marketingplatformadmin.googleapis.com`)
- Display & Video 360 API (`displayvideo.googleapis.com`)
- DoubleClick Bid Manager API (`doubleclickbidmanager.googleapis.com`)
- Campaign Manager 360 API (`dfareporting.googleapis.com`)
- Search Ads 360 Reporting API (`searchads360.googleapis.com`)

Configure the Google OAuth consent screen, add your account as a test user if
using Testing mode, and create an OAuth client of type **Desktop app**. The Google
account must already have access to the relevant products. OAuth consent alone
does not grant product access. CM360 also requires an API-enabled user profile.

Add this configuration to a stdio MCP client such as Claude Desktop, replacing
the checkout path and OAuth values:

```json
{
  "mcpServers": {
    "flin-gmp-mcp": {
      "command": "uv",
      "args": [
        "run", "--directory", "/absolute/path/to/flin-gmp-mcp",
        "--locked", "flin-gmp-mcp"
      ],
      "env": {
        "GOOGLE_CLIENT_ID": "your-desktop-client-id",
        "GOOGLE_CLIENT_SECRET": "your-desktop-client-secret"
      }
    }
  }
}
```

Restart your MCP client. Then ask it to:

1. Run `health_check`.
2. Run `authenticate`, finish Google sign-in in the browser, and grant the requested permissions.
3. Discover IDs using `list_organizations`, `list_dv360_partners`,
   `list_cm360_profiles`, or `list_sa360_customers`.
4. Use those IDs in the corresponding data tools.

`authenticate` waits up to 180 seconds; configure a longer tool timeout in your
client if necessary. It requires a browser on the computer running the server.
Data tools never launch a browser; they return `oauth_required` when sign-in is
needed. Access tokens refresh automatically. Use `authenticate(force=true)` to
replace a stale login or switch the selected account. No secrets are returned.

## Install from PyPI

```bash
uvx flin-gmp-mcp@0.1.1
```

In an MCP client, use `command: "uvx"` with `args: ["flin-gmp-mcp@0.1.1"]`
and the same Google environment variables shown above.

## macOS desktop installation

Download `flin-gmp-mcp-0.1.1.mcpb` from the
[v0.1.1 release](https://github.com/flin-agency/flin-gmp-mcp/releases/tag/v0.1.1)
and import it into Claude Desktop. The package includes the server and locked
dependency definitions; the first launch needs internet access. Enter your own
Google OAuth credentials in the extension settings.

See [macOS instructions](docs/desktop-extension.md), [privacy](PRIVACY.md) and
[support](SUPPORT.md). The bundle is unsigned and accompanied by a SHA-256 checksum.

## Configuration

| Variable | Required | Meaning |
| --- | --- | --- |
| `GOOGLE_CLIENT_ID` | Yes | Desktop OAuth client ID, same convention as flin Search Console |
| `GOOGLE_CLIENT_SECRET` | Yes | Desktop OAuth client secret |
| `GOOGLE_GMP_SERVICES` | No | Comma-separated subset of `admin,dv360,cm360,sa360`; defaults to all |
| `GOOGLE_GMP_TOKEN_DIR` | No | Absolute path to a dedicated private token directory |
| `GOOGLE_GMP_OAUTH_PORT` | No | Loopback port; `0` chooses an available port |
| `GOOGLE_GMP_QUOTA_PROJECT` | No | Optional quota project ID, sent as `x-goog-user-project` |

Environment variables are read from the process. `.env.example` is a reference;
`.env` files are **not automatically loaded**.

Only enabled products' scopes are requested. Disabled products return a
configuration error. After adding a product, run `authenticate` again to grant its
scopes. A token created by a different OAuth client is rejected.

### Multiple accounts and token storage

Pass `account="work"` to `authenticate` and subsequent calls to use a separate
Google login. Aliases use lower-case letters, digits, `_` and `-`, start with a
letter or digit, and have at most 64 characters. Omit `account` for the default
login; the name `default` is reserved.

Default directories:

- macOS: `~/Library/Application Support/flin-gmp-mcp/`
- Linux: `$XDG_CONFIG_HOME/flin-gmp-mcp/` or `~/.config/flin-gmp-mcp/`
- Windows: `%APPDATA%\flin-gmp-mcp\`

The default token is `default.json`; named accounts use `<account>.json`. Writes
are atomic and files use mode `0600` on POSIX. New directories use `0700`. Existing
directories must be owned by the user and not writable by others. Never commit
these files. To disconnect locally, stop the server and delete the corresponding
token file; revoke the app in your Google account to invalidate its access.

## OAuth scopes and read-only boundary

| Product | Scope suffixes under `https://www.googleapis.com/auth/` |
| --- | --- |
| GMP Admin | `marketingplatformadmin.analytics.read` |
| DV360 | `display-video`, `doubleclickbidmanager` |
| CM360 | `dfatrafficking`, `dfareporting` |
| SA360 | `doubleclicksearch` |

Google's 360 APIs require scopes that can also permit writes. The MCP enforces
read-only behavior with a fixed endpoint/method allowlist: GET requests and only
SA360 reporting/field-search POST requests. Use read-only product roles wherever
available for an additional account-level boundary. Authentication writes local
credentials and is annotated separately from read-only data tools.

## Results and pagination

Data tools return `{ "ok": true, "service": "...", "account": "...", "data": {...} }`.
`data` preserves Google's native response, including field masks, currencies,
report statuses and `nextPageToken`. The list key varies by API (`organizations`,
`advertisers`, `items`, `results`, etc.). Empty responses are valid.

Each list/search call returns **one page**. If `data.nextPageToken` is present,
pass it as `page_token` with all other arguments unchanged. Do not report the
first page as the full account total. Limits: DV360 200, Bid Manager 100,
GMP Admin 1000, CM360 1000 (local cap), SA360 data search 10000. Responses over
10 MiB are rejected; reduce the page size or selected fields. Requests have a
10-second connection and 60-second read timeout, with no automatic quota retries.

SA360 IDs are bare digits without hyphens. `login_customer_id` selects the manager
through which access is granted. `list_sa360_customers` lists directly accessible
customers only; `get_sa360_customer_clients` discovers manager children.
`get_sa360_campaign_performance` uses inclusive account-timezone dates and returns
`costMicros` in millionths of `customer.currencyCode`.

## Development

```bash
uv sync --locked --extra dev
uv run ruff check .
uv run pytest
uv build
```

Tests use mocked Google responses, including transport/authentication failures,
request contracts and a real local MCP stdio handshake. No Google credentials
are required. Live product access must be verified separately with your account.

- [Tool reference and examples](docs/mcp-usage-guide.md)
- [Testing and live verification](docs/testing.md)
- [Release checklist](docs/release.md)

## References

Implementation conventions follow
[flin Search Console](https://github.com/flin-agency/flin-google-search-console-mcp)
and [flin Google Ads](https://github.com/flin-agency/flin-google-ads-mcp).

Verified against Google's REST references and live discovery documents:

- [GMP Admin API](https://developers.google.com/marketing-platform/devguides/api/admin/v1/rest)
- [DV360 v4](https://developers.google.com/display-video/api/reference/rest/v4/advertisers/list)
- [Bid Manager v2](https://developers.google.com/bid-manager/reference/rest/v2/queries.reports/list)
- [CM360 v5](https://developers.google.com/doubleclick-advertisers/rest/v5)
- [SA360 Reporting v0](https://developers.google.com/search-ads/reporting/api/reference/rest)
- [Desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app)

MIT © flin GmbH.
