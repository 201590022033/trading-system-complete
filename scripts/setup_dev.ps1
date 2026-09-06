# Run from any directory. No execution-policy, system-software or secret changes.
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 "$PSScriptRoot/setup_dev.py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$PSScriptRoot/setup_dev.py"
} else {
    throw 'Python 3.12 is required. Install it, then run this script again.'
}
if ($LASTEXITCODE -ne 0) { throw 'Development setup failed; review the reported check.' }
