param(
    [int]$Port = 5000,
    [string]$ReportDirectory = ''
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
Push-Location $dashboardRoot
try { & $dashboardPython app.py }
finally { Pop-Location }
