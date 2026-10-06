# Main local dashboard installation and navigation

Completed 6 October 2026. The clean main checkout was fast-forwarded from c27488b to the tested R1 commit 590cbf5, preserving its ignored runtime/configuration files. Portfolio & demo is now last; Trading Strategies is first and opens by default. Account/journal controls and research behavior are preserved.

`scripts/start_dashboard.ps1` starts the actual app on loopback port 5000 using the existing project Python environment and `runtime/local-backtest/dashboard-summary.json`. The dated sanitized summary was installed in that ignored directory. An optional ReportDirectory parameter chooses another trusted report directory. This is the main local app, not the earlier stubbed preview. Hosted/Railway deployment is outside this installation.

Browser checks covered all six workspaces: strategy profiles and B5 evidence, canonical five-card ranking, news/source registry, technical workspace, System and the relocated cash/journal workspace. Public index history and Moneyweb/SENS feeds loaded. Local research still waits for collected data; no daily worker brief exists in this runtime. IG's actual account endpoint returned CREDENTIALS_MISSING with live_execution false. Required IG_API_KEY, IG_IDENTIFIER (or legacy username) and IG_PASSWORD were absent; no history entitlement request was possible. No credentials or account values were exported.

The first test run failed because of memory-allocation errors while the dashboard/browser were active. With dashboard processes paused and numerical-library threads bounded to one, the full 926-test safe suite passed in 87.585 seconds. This environmental failure did not require a code change. The legacy engine/admission boundaries remain unchanged.

Start from PowerShell at the main checkout:

```powershell
./scripts/start_dashboard.ps1
```

The local server must keep running for the browser to work. No cloud deployment, broker order or worker schedule change was performed.
