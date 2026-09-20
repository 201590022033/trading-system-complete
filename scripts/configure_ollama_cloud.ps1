[CmdletBinding()]
param(
    [string]$Model = 'gpt-oss:20b',
    [string[]]$Services = @('trading-system-complete', 'trading-worker')
)

$ErrorActionPreference = 'Stop'

$railway = Get-Command railway.cmd -ErrorAction SilentlyContinue
if (-not $railway) {
    $candidate = Join-Path $env:APPDATA 'npm\railway.cmd'
    if (Test-Path -LiteralPath $candidate) { $railway = Get-Item -LiteralPath $candidate }
}
if (-not $railway) { throw 'railway.cmd was not found. Install/login to the Railway CLI first.' }

& $railway.Source status | Out-Host
$secureKey = Read-Host 'Paste the replacement Ollama Cloud API key' -AsSecureString
$keyPointer = [IntPtr]::Zero
$plainKey = $null
try {
    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)

    foreach ($service in $Services) {
        Write-Host "Configuring Ollama Cloud for $service..."
        & $railway.Source variable set --service $service "OLLAMA_CLOUD_MODEL=$Model" | Out-Host
        $plainKey | & $railway.Source variable set --service $service OLLAMA_API_KEY --stdin | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "Railway rejected the Ollama key for $service." }
    }
    Write-Host 'Ollama Cloud configuration completed without printing the key.'
}
finally {
    if ($keyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    }
    $plainKey = $null
    $secureKey = $null
}
