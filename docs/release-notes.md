## New in 0.1.3

DV360 performance can now be retrieved without manually preparing a report:
create a saved STANDARD CSV query, start it asynchronously, check its status,
and read the completed CSV records through MCP.

- `create_dv360_report_query`: choose advertiser, metrics, dimensions and dates;
  defaults to yesterday, impressions and clicks. New queries disable email and sharing.
- `run_dv360_report`: start an existing query without blocking until completion.
- `read_dv360_report_rows`: retrieve bounded CSV pages while preserving precision,
  headers, totals, currencies and footer records.
- Slow Google requests and browser sign-in no longer block the MCP event loop.
- Campaigns, budgets, bids, targeting and creatives remain protected from writes.
  Only DV360 report creation and execution have been added to the POST allowlist.

The server exposes 32 tools. Existing desktop bundles from 0.1.2 update the server
from PyPI on restart when automatic updates are enabled. Otherwise install the
new `.mcpb` below or run `uvx flin-gmp-mcp@0.1.3`.

Validation: 171 automated tests, lint/format checks, Python package builds and
metadata validation, plus desktop bundle startup/tool discovery. Live DV360 report
creation and data comparison have not been tested with an authorized Google account.
CSV downloads are limited to 10 MiB and 1000 records per call. Report creation/runs
must not be blindly retried after a timeout; check existing queries/runs first.
