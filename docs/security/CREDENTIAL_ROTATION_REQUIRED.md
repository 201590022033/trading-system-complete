# Credential Rotation Required

Repository history contains a credential-like literal in a historical version
of a development helper. Treat that credential as compromised: revoke and rotate
it with the provider, review provider access logs and billing, and use environment
or secret-manager injection thereafter.

Do not copy the historical value into issues, logs, documentation, commits, or
chat. OI2 does not read `.env`, expose credential values, or require credentials
for its default offline path. Removing a value from the current file does not
remove it from Git history; history remediation should be a separately approved,
coordinated operation.
