## Automatic desktop updates — 0.1.5

**Automatic server updates are enabled by default again.** Restart Claude Desktop
or the connector after a release to load the latest compatible stable server from
PyPI. Normal server updates do not require reinstalling the `.mcpb`.

Already installed 0.1.4? Enable **Automatic server updates** once in its settings,
then restart. The existing bundle can load this and future compatible server
releases directly from PyPI. No new bundle installation is needed for this change.

For new installations, download **flin-gmp-mcp-0.1.5.mcpb** below. Every server
release continues to publish **both PyPI and a new Claude Desktop bundle**.

- Explicit package upgrades refresh cached PyPI metadata on startup.
- New post-publication checks require the new and baseline 0.1.4 bundles to start
  the exact newly published PyPI version before the GitHub release is published.
- A bundled fallback or old cached version cannot pass the update check.
- `health_check` reports the running server version even before Google setup.
- Token-storage hardening, updater environment isolation, dependency auditing,
  pinned Actions and Apple Silicon/Intel startup checks remain in place.

Validation: 193 tests, Python package checks and real MCP bundle startup. The release
also requires live PyPI update checks for new and older bundles. All 32 tools remain
available. Updates happen on restart, not during a running session. Major version
1.x or changes to the launcher/manifest/permissions can require a new bundle.

The bundle is unsigned; **SHA256SUMS**, **SECURITY-REVIEW.md** and
**dependency-audit.json** accompany it. Live authenticated Google product behavior
and interactive Claude Desktop installation have not been tested.
