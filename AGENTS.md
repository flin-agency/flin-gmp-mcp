# Release requirements

Every server release must publish the matching version to **both PyPI and GitHub**,
including a newly built Claude Desktop `.mcpb` and its SHA-256 checksum. Use the tag
release workflow; a GitHub-only bundle is not a completed server release.

Automatic PyPI server updates in the desktop extension must remain enabled by
default. This is an explicit user requirement. Do not turn them off as generic
security hardening. Preserve credential isolation, stable-version bounds, timeouts
and cached/bundled fallbacks. Normal compatible server updates must take effect
after a connector restart without reinstalling the desktop bundle.

Before confirming publication, verify the public PyPI runtime through the new
desktop bundle and through the baseline `v0.1.4` bundle with updates enabled.
Require the expected running server version and the PyPI launch diagnostic;
successfully starting an old bundled fallback does not prove an update worked.
Launcher, manifest or permission changes can still require a bundle update; state
that limit accurately. Existing v0.1.4 installs need automatic updates enabled once.
