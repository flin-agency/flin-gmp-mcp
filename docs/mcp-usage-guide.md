# Tool reference

All data tools accept optional `account`. Call `authenticate` once before reading data.

| Tool | Purpose |
| --- | --- |
| `health_check` | Check local configuration and token status. No Google request or browser launch. |
| `authenticate` | Sign in via the local browser and store credentials privately; never returns tokens. |
| `list_organizations` | List accessible GMP organizations (one page, max 1000); not Google Cloud organizations. |
| `get_organization` | Get a GMP organization by ID or organizations/{id} from list_organizations. |
| `list_analytics_account_links` | List Analytics accounts linked to a GMP organization; no GA4 performance data. |
| `list_dv360_partners` | Discover DV360 partners (max 200 per page). Optional native DV360 filter. |
| `list_dv360_advertisers` | List advertisers for a discovered partner ID (required by DV360 v4; max 200). |
| `get_dv360_advertiser` | Read one DV360 advertiser's settings. |
| `list_dv360_campaigns` | List DV360 campaigns settings (max 200). These are not performance metrics. |
| `list_dv360_insertion_orders` | List DV360 insertion orders settings (max 200). These are not performance metrics. |
| `list_dv360_line_items` | List DV360 line items settings (max 200). These are not performance metrics. |
| `list_dv360_creatives` | List DV360 creatives settings (max 200). These are not performance metrics. |
| `list_dv360_report_queries` | List existing DV360 report definitions via Bid Manager v2 (max 100). No report creation. |
| `list_dv360_reports` | List existing runs of a DV360 report query, including available report metadata/URLs. |
| `get_dv360_report` | Get an existing DV360 report's status and metadata, including its URL when available. |
| `list_cm360_profiles` | Discover accessible CM360 user profiles. Choose profileId for subsequent CM360 tools. |
| `list_cm360_advertisers` | List CM360 advertisers for a user profile; optional native name/ID search with * wildcards. |
| `list_cm360_campaigns` | List CM360 campaigns. Omit archived for both active and archived campaigns. |
| `list_cm360_creatives` | List CM360 creatives with names, types, sizes and asset metadata; filter by advertiser or campaign. |
| `get_cm360_creative` | Get full CM360 creative metadata, including backup-image asset identifiers and available serving URLs. |
| `list_cm360_reports` | List saved CM360 report definitions visible to this profile. Does not execute reports. |
| `list_cm360_report_files` | List existing CM360 report files and their status; no new report is generated. |
| `get_cm360_report_file` | Get existing CM360 report file metadata and download URLs; does not download CSV content. |
| `list_sa360_customers` | List directly accessible SA360 customer resource names. Use get_sa360_customer_clients |
| `query_sa360` | Run a read-only Search Ads 360 SELECT query and return one page (max 10000). |
| `get_sa360_customer_clients` | Discover client accounts beneath an SA360 manager, including hierarchy levels. |
| `get_sa360_campaign_performance` | Campaign impressions, clicks, cost_micros, conversions and conversion value. |
| `search_sa360_fields` | Discover SA360 query fields and compatibility using a metadata SELECT without FROM. |
| `list_sa360_custom_columns` | List custom columns available to an SA360 customer. |

## Example calls

```json
{"tool": "authenticate", "arguments": {"account": "work"}}
```

```json
{"tool": "list_analytics_account_links", "arguments": {"organization": "organizations/YOUR_ORG_ID", "account": "work"}}
```

```json
{"tool": "list_dv360_advertisers", "arguments": {"partner_id": "123", "page_size": 50, "account": "work"}}
```

```json
{"tool": "list_cm360_campaigns", "arguments": {"profile_id": "123", "advertiser_id": "456", "archived": false, "account": "work"}}
```

```json
{"tool": "get_sa360_campaign_performance", "arguments": {"customer_id": "1234567890", "login_customer_id": "9876543210", "start_date": "2026-10-01", "end_date": "2026-10-29", "segment_by_date": true, "account": "work"}}
```

```json
{"tool": "query_sa360", "arguments": {"customer_id": "1234567890", "query": "SELECT campaign.id, campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS", "page_size": 100, "account": "work"}}
```

IDs above are placeholders; use discovery tools to obtain your actual IDs.
The `tool`/`arguments` objects illustrate tool calls, not terminal commands.

## Operational notes

- Keep account aliases consistent throughout discovery and reporting.
- Google returns IDs and some numeric metrics as strings; preserve their precision.
- Preserve `data.nextPageToken`; Google may return fewer rows than the requested
  page size even when more pages exist.
- A report's URL may only become available after its status is complete. This
  server does not trigger generation, poll indefinitely, or fetch external URLs.
- Use SA360 field discovery before constructing queries with unfamiliar fields.
  Custom queries are validated by Google's reporting service.
- `health_check` reports saved-token state, not live account authorization.
- Raw upstream error bodies are intentionally omitted because they can include
  sensitive data. API errors expose a stable code and suggested next steps.

## CM360 creative assets and previews

Use `list_cm360_creatives(profile_id, advertiser_id=..., campaign_id=...)` to
find creatives associated with a campaign. Filters are optional; `creative_ids`,
`types`, `search`, `active` and `archived` can narrow the result. Continue with
`page_token` and the same filters. Use `get_cm360_creative(profile_id, creative_id)`
for an individual creative. Both preserve Google's complete metadata, including
`name`, `type`, `size`, `additionalSizes` and `creativeAssets` when present.

For a creative gallery, show name, format and dimensions. Inspect assets with
`role == "BACKUP_IMAGE"` for HTML5 fallback-image metadata (identifier, filename,
size). Missing fields/assets remain missing; do not assume every result contains
a backup. A filename or asset ID is not a usable image URL.

The [v5 Creative schema](https://developers.google.com/doubleclick-advertisers/rest/v5/creatives)
does not document a backup-image download or preview URL. The
[creativeAssets resource](https://developers.google.com/doubleclick-advertisers/rest/v5/creativeAssets)
only exposes insertion, not download. `progressiveServingUrl` and
`streamingServingUrl` are documented for video assets, not HTML5 backups.
Click-through URLs, tracking URLs and `redirectUrl` must not be used as thumbnails.
Do not guess CDN URLs from filenames or execute returned `htmlCode`.

Until an actual usable image URL or separately supplied image is available, show
an explicit “Preview unavailable” placeholder alongside the metadata. The connector
returns JSON metadata, not image bytes, extracted ZIPs or an HTML5 renderer.
The existing CM360 `dfatrafficking` scope covers both new calls.

Live verification still requires an authorized CM360 account: local configuration
was missing during implementation, so no claim is made that real backup-image
files can be retrieved. Follow the smoke test in `testing.md`.
