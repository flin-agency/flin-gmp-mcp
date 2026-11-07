# Support

Start with `connection_status`. It reports the running server version, local
configuration and the next action without opening a browser or calling Google.
`auth_status: unknown` with a local token is normal until access is actually checked;
`live_access: not_checked` is not an error. Use the README's product-specific read
to test Google access after `authenticate`.

- Incomplete setup: obtain the required fields from your administrator/password manager.
- Sign-in needed: run `authenticate` and finish Google consent on this computer.
- Permission denied: check product membership, enabled APIs, scopes and quota.
- Cache/bundled fallback: check internet access and restart the connector to retry.
- Incorrect account: use the same account alias for authentication and data tools.

Report problems via [GitHub issues](https://github.com/flin-agency/flin-gmp-mcp/issues)
or **flin@flin.agency**. Include `server_version`, extension version if available,
Mac architecture/OS, tool name and sanitized error code. Never include secrets,
tokens, customer data or unredacted logs. Security reports should be private.

To remove access, stop/remove the extension, clear its saved settings in Claude,
delete this MCP's local tokens and revoke Google authorization. See [PRIVACY.md](PRIVACY.md)
for storage paths and [desktop setup](docs/desktop-extension.md) for update behavior.
