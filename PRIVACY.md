# Privacy

The flin Google Marketing Platform MCP runs locally. It has no flin-hosted service,
telemetry, analytics, or advertising tracking.

- OAuth client settings come from your MCP client's configuration.
- Browser authentication communicates with Google. Access and refresh tokens are
  stored in a private local directory, described in the README. They are never
  returned by MCP tools or included in the desktop bundle.
- Data requests go to Google's Marketing Platform Admin, Display & Video 360,
  Bid Manager, Campaign Manager 360 and Search Ads 360 APIs, as enabled by you.
- Requested account, campaign and report data is returned to your MCP client.
  That client's data policies apply to its use of the results.
- Installing the desktop bundle may download Python and locked dependencies
  through uv. These downloads do not contain your Google tokens or report data.
- Delete local token files to remove saved sign-ins; revoke the application's
  access in your Google account to invalidate its authorization.

Contact: flin@flin.agency. Google's processing is governed by
[Google's privacy policy](https://policies.google.com/privacy).
