## New in 0.1.2

The desktop extension now checks PyPI at each connector start and loads the latest
stable 0.x server automatically. Install this bundle once to enable future updates;
restart Claude or the connector after publishing a new server version.

- Dynamic tool discovery includes new server tools without reinstalling the bundle.
- Bounded update checks fall back to cached or bundled code if unavailable.
- Existing Google settings and saved sign-ins are preserved.
- Disable automatic updates in extension settings to use only the bundled version.
- The included server provides 29 tools, including CM360 creative list/detail queries.
  HTML5 backup-image downloads remain unverified; these tools return asset metadata.

Download the `.mcpb` below for Claude Desktop, or run `uvx flin-gmp-mcp@0.1.2`.
The extension version identifies the launcher; `health_check.version` shows the
actual server version. Updates to the launcher itself require another bundle install.
