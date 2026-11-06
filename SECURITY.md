# Security review — 0.1.5 (including 0.1.4 hardening)

Reviewed on 2026-11-06: runtime source, OAuth flow, local token storage, Google
request boundaries, report downloads, desktop launcher, dependencies, bundle
contents and GitHub publication workflow. This is a source and automated review,
not an independent penetration test or a guarantee of freedom from vulnerabilities.

## Findings addressed

- **Dependencies:** upgraded OAuthLib 4.0.0 to 4.0.1 and pytest 8.4.2 to 9.2.0.
  [OAuthLib's advisory](https://github.com/oauthlib/oauthlib/security/advisories/GHSA-3jp2-3mrg-2vxc)
  concerns a server-side device grant that this Google OAuth client does not use;
  the affected dependency was nevertheless replaced and its minimum version raised.
  [pytest's advisory](https://github.com/pytest-dev/pytest/security/advisories/GHSA-6w46-j5rx-g56g)
  concerns temporary-directory handling in development/test environments. pytest
  is not installed by the desktop runtime. The scanner reported that advisory twice;
  there were two distinct advisories, not three independent vulnerabilities.
- **Token reads:** validate directory and file ownership and private POSIX modes
  before parsing credentials. Use directory-relative descriptors and `O_NOFOLLOW`
  on macOS/Linux to reject symlink swaps. Reject non-regular files, hard links and
  files exceeding 64 KiB. Nonblocking opens reject FIFOs without hanging. Atomic
  writes retain `0600` without a subsequent path-based permission change.
- **Desktop updates:** automatic stable PyPI updates are enabled by default, as
  explicitly required for this project. New compatible server releases load on
  connector restart without reinstalling the bundle. The update probe still
  receives only allowlisted OS environment settings. Explicit package upgrades
  refresh cached metadata. Users can disable updates to pin bundled code.
  Existing 0.1.4 installs need the setting enabled once. Release checks prove that
  both the current and baseline 0.1.4 launchers run the exact new PyPI version;
  falling back to bundled code fails the update check.
- **Publication:** pin third-party Actions by full commit, disable persisted Git
  checkout credentials, audit hashed locked dependencies before publishing, and
  require real bundle startup on Apple Silicon and Intel macOS runners before
  the PyPI/GitHub release jobs. A post-publication PyPI update check additionally
  gates the GitHub release. PyPI uses short-lived OIDC authentication.

## Verification

- 193 automated tests, including unsafe permission/ownership cases, a symlink-swap
  regression, special files, token size bounds, default updates and strict
  update verification.
- Ruff lint and format checks; Python wheel/source build and metadata validation.
- pip-audit 2.10.1 against the installed development environment and hashed locked
  dependencies: no known vulnerabilities after remediation. GitHub reruns the
  audit at release time and attaches `dependency-audit.json`.
- The initial 0.1.4 review ran Gitleaks 8.30.1 across all five preceding commits
  and the packaged bundle: no secrets detected.
- Bandit static review: no high-severity findings. The SQL-string warning refers
  to the fixed SA360 query whose variable dates are parsed and round-trip validated;
  no raw query input is interpolated there. Low-severity subprocess warnings refer
  to explicit argument arrays without a shell in the updater. Password
  literal warnings are the public Google token URL and token-presence booleans.
- Reproducible MCPB packaging from allowlisted files, schema validation, checksum,
  and actual stdio startup/tool discovery/health check without Google credentials.

## Security boundaries and remaining limits

The server uses local stdio; it does not expose an HTTP MCP listener. Interactive
Google sign-in uses PKCE/state and a temporary loopback callback. Tokens are stored
as private local JSON files, not encrypted in Keychain. Claude's sensitive OAuth
client-secret setting uses its own protected settings storage.

Google API methods and paths are allowlisted. No campaign mutations or arbitrary
URLs are exposed. DV360 report creation/execution are explicitly annotated writes;
running a pre-existing report can use its existing notification settings. Google
360 OAuth scopes can permit broader operations than this server exposes.

Report downloads accept only HTTPS `storage.googleapis.com`, without redirects,
OAuth forwarding or ambient netrc credentials, with a 10 MiB limit. API/report data
is untrusted input to the consuming assistant. The consuming client must decide
which tools to invoke and whether data may be shared elsewhere.

The local OS account, installed Python/uv runtime, upstream package registries,
Google and the MCP client remain trust dependencies. The updater's environment
allowlist is not an OS sandbox. This review does not protect against an attacker
who already controls the same user account, writable ancestor directories or root.
POSIX ownership/mode guarantees apply to macOS/Linux; Windows ACLs are not audited
and this desktop bundle declares macOS support only.

The MCPB is unsigned; SHA-256 checks detect corruption, not a compromised release
publisher. No interactive Claude Desktop installation or authenticated live Google
product test was performed. Automated MCP startup does not establish product access,
consent correctness in a real account, quota availability or live report accuracy.

## Reporting

Report suspected vulnerabilities privately to **flin@flin.agency**. Include the
version and reproduction steps; never include OAuth tokens or customer report data.
