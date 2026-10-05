# Credential Rotation Required

## Current context — 5 October 2026

The requirements below remain governing constraints. This reconciliation adds navigation/current context without weakening the original safety or evidence rules.

The current dashboard has six sections including backend-populated Trading Strategies and the canonical Top-5. Older multi-agent/mock/merge designs remain historical context; they do not describe the default ranking path. Paper/connected cash and self-reported trades stay separate. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Repository history contains a credential-like literal in a historical version
of a development helper. Treat that credential as compromised: revoke and rotate
it with the provider, review provider access logs and billing, and use environment
or secret-manager injection thereafter.

Do not copy the historical value into issues, logs, documentation, commits, or
chat. OI2 does not read `.env`, expose credential values, or require credentials
for its default offline path. Removing a value from the current file does not
remove it from Git history; history remediation should be a separately approved,
coordinated operation.
