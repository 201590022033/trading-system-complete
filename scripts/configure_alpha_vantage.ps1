[CmdletBinding()]
param(
    [switch]$LocalOnly,
    [switch]$UseSavedLocalKey,
    [string]$Project = '3b1413d7-35d9-4a43-ba34-fdfb3331989c',
    [string]$Environment = 'production',
    [string[]]$Services = @('trading-system-complete', 'trading-worker')
)
$ErrorActionPreference = 'Stop'
try { $Host.UI.RawUI.WindowTitle = 'Alpha Vantage private key setup' } catch { }
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$envPath = Join-Path $repoRoot '.env'
if (-not $LocalOnly) {
    $railwayCommand = Get-Command railway.exe -ErrorAction SilentlyContinue
    if (-not $railwayCommand) { $railwayCommand = Get-Command railway.cmd -ErrorAction Stop }
}
Write-Host "Local key destination: $envPath (ignored by Git)."
Write-Host 'Railway changes will skip deployments; existing services keep running.'
$secureKey = $null
$keyPointer = [IntPtr]::Zero
$plainKey = $null
try {
    if ($UseSavedLocalKey) {
        $saved = [regex]::Matches([IO.File]::ReadAllText($envPath), '(?m)^ALPHA_VANTAGE_API_KEY=([A-Za-z0-9]+)\r?$')
        if ($saved.Count -ne 1) { throw 'One previously saved local Alpha Vantage key is required.' }
        $plainKey = $saved[0].Groups[1].Value
        $saved = $null
    } else {
        $secureKey = Read-Host 'Paste your Alpha Vantage API key (hidden)' -AsSecureString
        $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
        $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer).Trim()
    }
    if ($plainKey -notmatch '^[A-Za-z0-9]{8,128}$' -or $plainKey -eq 'demo') {
        throw 'Expected a private alphanumeric Alpha Vantage key.'
    }
    & git -C $repoRoot check-ignore --quiet .env
    if ($LASTEXITCODE -ne 0) { throw 'Refusing to save a key: .env is not ignored.' }
    # Read privately to preserve existing IG/Ollama settings. Never display content.
    $existing = if (Test-Path -LiteralPath $envPath) { [IO.File]::ReadAllText($envPath) } else { '' }
    $existing = [regex]::Replace($existing, '(?m)^\s*ALPHA_VANTAGE_(API_KEY|ENABLED)\s*=.*\r?\n?', '')
    [IO.File]::WriteAllText($envPath, $existing.TrimEnd()+"`r`nALPHA_VANTAGE_API_KEY=$plainKey`r`nALPHA_VANTAGE_ENABLED=0`r`n", [Text.UTF8Encoding]::new($false))
    Write-Host 'Local key saved; scheduled local calls stay off. The explicit probe has a five-call budget.'
    if (-not $LocalOnly) {
        foreach ($service in $Services) {
            # Windows PowerShell 5 treats native stderr warnings as ErrorRecords.
            # CLI exit status, not a deprecation warning, determines success.
            $ErrorActionPreference = 'Continue'
            $plainKey | & $railwayCommand.Source variable set ALPHA_VANTAGE_API_KEY --stdin --skip-deploys --service $service --environment $Environment --project $Project *> $null
            $keyExitCode = $LASTEXITCODE
            $ErrorActionPreference = 'Stop'
            if ($keyExitCode -ne 0) { throw "Railway key update failed for $service; local configuration is saved." }
            $ErrorActionPreference = 'Continue'
            & $railwayCommand.Source variable set ALPHA_VANTAGE_ENABLED=1 --skip-deploys --service $service --environment $Environment --project $Project *> $null
            $enabledExitCode = $LASTEXITCODE
            $ErrorActionPreference = 'Stop'
            if ($enabledExitCode -ne 0) { throw "Railway enable setting failed for $service." }
            Write-Host "Railway configuration saved for $service without deploying."
        }
    }
    Write-Host 'Key setup complete. Verify actual JSE coverage before claiming data availability.'
    $receiptPath = Join-Path $repoRoot '.cache\alpha-vantage-setup-status.json'
    [IO.Directory]::CreateDirectory((Split-Path $receiptPath)) > $null
    @{ local_key_saved = $true; railway_key_saved = (-not $LocalOnly); deployment_triggered = $false } |
        ConvertTo-Json | Set-Content -LiteralPath $receiptPath
}
finally {
    if ($keyPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer) }
    $plainKey = $null
    $secureKey = $null
    $existing = $null
}
