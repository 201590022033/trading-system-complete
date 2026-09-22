param(
    [Parameter(Mandatory = $true)]
    [string]$PythonPath
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "load_local_env.ps1")
$env:HOST = "127.0.0.1"

& $PythonPath (Join-Path $PSScriptRoot "..\app.py")
exit $LASTEXITCODE
