# Privacy

The flin Google Marketing Platform MCP runs locally. It has no flin-hosted service,
telemetry, analytics, or advertising tracking.

- OAuth client settings come from your MCP client's configuration.
- Browser authentication communicates with Google. Access and refresh tokens are
  stored as **unencrypted JSON files** in a private local directory, described in
  the README. Claude protects its own sensitive settings separately. Tokens are never
  returned by MCP tools or included in the desktop bundle.
- Data requests go to Google's Marketing Platform Admin, Display & Video 360,
  Bid Manager, Campaign Manager 360 and Search Ads 360 APIs, as enabled by you.
- Creating a DV360 report saves its title, advertiser filter, fields and date range
  at Google. Running it creates a report file. New queries disable email and sharing;
  existing queries retain their notification settings. No campaign settings are changed.
- Reading DV360 CSV values downloads the completed file from Google Cloud Storage
  into memory and returns its records; the MCP does not save the file locally.
- Requested account, campaign and report data is returned to your MCP client.
  That client's data policies apply to its use of the results.
- Starting the desktop extension checks PyPI for stable compatible server updates
  by default. Package downloads use PyPI and its file hosts through uv. The update
  probe receives only allowlisted operating-system environment settings, excluding
  Google and other cloud secrets. This does not restrict its filesystem access.
  Updates execute newly published server code; they can be disabled in extension
  settings. Existing 0.1.4 installations need the setting enabled once.
- Installing the desktop bundle may download Python and locked dependencies
  through uv. These downloads do not contain your Google tokens or report data.
- To disconnect: stop/remove the extension, remove its saved client settings in
  Claude, delete the relevant token file(s) and revoke the application's access in
  your Google account. Removing the extension alone may leave token files behind.
  The default Mac directory is `~/Library/Application Support/flin-gmp-mcp/`;
  `GOOGLE_GMP_TOKEN_DIR` can override it. `default.json` and `<account>.json` store
  separate sign-ins. Remove only this MCP's files. Other platform paths are in the README.
- `connection_status` reads local setup only: it sends no Google request, refreshes
  no token and starts no browser. A saved token is not proof of live Google access.

Contact: flin@flin.agency. Google's processing is governed by
[Google's privacy policy](https://policies.google.com/privacy).
