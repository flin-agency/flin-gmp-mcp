## New in 0.1.1

- Add `list_cm360_creatives` and `get_cm360_creative` with names, formats,
  dimensions and complete asset metadata.
- Filter creatives by advertiser, campaign, IDs, type, name and status; support pagination.
- Document HTML5 backup-image identification and preview limitations. The API does
  not document a backup-image download endpoint. Live image retrieval remains unverified.
- Validate the new routes against Google Discovery; 123 automated tests pass.

Read-only Google Marketing Platform MCP with 29 tools for GMP Admin, Display &
Video 360, Campaign Manager 360 and Search Ads 360. Includes browser OAuth,
separate Google accounts, pagination and private local token storage.

## Install

- **macOS / Claude Desktop:** Download the `.mcpb` file below and open it with
  Claude Desktop. Enter your Google Desktop OAuth client ID and secret, then run
  `authenticate`. Python 3.12 and locked dependencies are managed through uv.
- **Other stdio MCP clients:** `uvx flin-gmp-mcp@0.1.1`.

The bundle needs internet on first launch and is not signed. `SHA256SUMS`
contains its checksum. Setup instructions are in `docs/desktop-extension.md`.

Automated checks cover all API routes, authentication failure cases, packaging,
and an actual MCP stdio handshake. Authenticated Google product access still
requires your own account and enabled APIs. DV360/CM360 report tools return
existing report metadata and URLs; SA360 returns performance rows directly.
