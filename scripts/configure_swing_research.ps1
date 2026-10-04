[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PythonPath, [switch]$ConfigureRailway)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $repoRoot '.env'
if (-not (Test-Path -LiteralPath $PythonPath)) { throw 'Project Python runtime is missing.' }
& git -C $repoRoot check-ignore --quiet .env
if ($LASTEXITCODE -ne 0) { throw 'Private configuration must be ignored.' }
$text = if (Test-Path -LiteralPath $envPath) { [IO.File]::ReadAllText($envPath) } else { '' }
$tokenMatch = [regex]::Match($text, '(?m)^SWING_DATA_UPLOAD_TOKEN=([a-f0-9]{64})\r?$')
$token = if ($tokenMatch.Success) { $tokenMatch.Groups[1].Value } else {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes); $rng.Dispose()
    -join ($bytes | ForEach-Object { $_.ToString('x2') })
}
$url = 'https://trading-system-complete-production.up.railway.app'
$text = [regex]::Replace($text, '(?m)^SWING_(DATA_UPLOAD_TOKEN|RESEARCH_URL)=.*\r?\n?', '')
[IO.File]::WriteAllText($envPath, $text.TrimEnd()+"`r`nSWING_DATA_UPLOAD_TOKEN=$token`r`nSWING_RESEARCH_URL=$url`r`n", [Text.UTF8Encoding]::new($false))
if ($ConfigureRailway) {
    foreach ($service in @('trading-system-complete','trading-worker')) {
        $ErrorActionPreference = 'Continue'
        $token | & railway.cmd variable set SWING_DATA_UPLOAD_TOKEN --stdin --skip-deploys --service $service *> $null
        $exitCode = $LASTEXITCODE; $ErrorActionPreference = 'Stop'
        if ($exitCode -ne 0) { throw 'Private Railway configuration update failed.' }
    }
}
# App collection schedule, separate from Codex reminders. No password stored.
$collector = Join-Path $repoRoot 'scripts\collect_swing_data.py'
$action = New-ScheduledTaskAction -Execute $PythonPath -Argument ('"'+$collector+'" --upload') -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -Daily -At '07:30'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'Trading System Local Swing Daily Data' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force > $null
Write-Host 'Private sync configuration saved. Local collection scheduled at 07:30 while signed in; missed runs start when available. Computer must be powered on.'
$token = $null; $text = $null
