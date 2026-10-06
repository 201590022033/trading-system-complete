param(
    [int]$Port = 5000,
    [string]$ReportDirectory = '',
    [switch]$Background
)
$ErrorActionPreference = 'Stop'
$dashboardRoot = Split-Path -Parent $PSScriptRoot
$dashboardPython = Join-Path $dashboardRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $dashboardPython)) { throw 'Project Python environment is missing.' }
if (-not $ReportDirectory) { $ReportDirectory = Join-Path $dashboardRoot 'runtime/local-backtest' }
$env:LOCAL_BACKTEST_REPORT_DIR = [IO.Path]::GetFullPath($ReportDirectory)
$env:HOST = '127.0.0.1'
$env:PORT = [string]$Port
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:OST_LOCAL_IMPORT_ENABLED = '1'
if ($Background) {
    $dashboardLogs = Join-Path $dashboardRoot 'runtime'
    New-Item -ItemType Directory -Path $dashboardLogs -Force | Out-Null
    $dashboardProcess = Start-Process -FilePath $dashboardPython -ArgumentList 'app.py' `
        -WorkingDirectory $dashboardRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $dashboardLogs 'dashboard.stdout.log') `
        -RedirectStandardError (Join-Path $dashboardLogs 'dashboard.stderr.log')
    [pscustomobject]@{ State = 'STARTED_IN_BACKGROUND'; ProcessId = $dashboardProcess.Id; URL = "http://127.0.0.1:$Port/" }
    exit 0
}
Push-Location $dashboardRoot
try { & $dashboardPython app.py }
finally { Pop-Location }
