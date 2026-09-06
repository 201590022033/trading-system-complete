param(
    [string]$Model = "llama3.2:3b",
    [switch]$CheckOnly,
    [switch]$InstallOllama,
    [switch]$PullModel,
    [switch]$SkipKimiKey
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = (Resolve-Path $root).Path
$envFile = Join-Path $root '.env'
$ollamaHost = 'http://127.0.0.1:11434'
$maxModelSizeGB = 5

function Write-Status($label, $state, $detail = '') {
    $line = "$label`: $state"
    if ($detail) { $line += " ($detail)" }
    Write-Output $line
}

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-OllamaExe {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'),
        (Join-Path $env:PROGRAMFILES 'Ollama\ollama.exe'),
        (Join-Path ${env:PROGRAMFILES(x86)} 'Ollama\ollama.exe')
    )
    foreach ($path in $candidates) {
        if (Test-Path $path -PathType Leaf) { return $path }
    }
    $inPath = Get-Command ollama -ErrorAction SilentlyContinue
    if ($inPath) { return $inPath.Source }
    return $null
}

function Get-OllamaVersion($exe) {
    if (-not $exe) { return $null }
    try {
        $raw = & $exe --version 2>$null
        if ($raw -match '([0-9]+\.[0-9]+\.[0-9]+)') { return $Matches[1] }
    } catch { }
    return $null
}

function Get-OllamaApiTags {
    try {
        $response = Invoke-RestMethod -Uri "$ollamaHost/api/tags" -TimeoutSec 3 -UseBasicParsing
        return @{ success = $true; names = @($response.models | ForEach-Object { $_.name }) }
    } catch {
        return @{ success = $false; names = @() }
    }
}

function Get-OllamaStatus {
    $status = [ordered]@{
        installed = $false
        version = $null
        running = $false
        reachable = $false
        state = 'NOT_INSTALLED'
        model_present = $false
        model = $Model
        models = @()
        exe = $null
    }
    $status.exe = Get-OllamaExe
    if ($status.exe) {
        $status.installed = $true
        $status.version = Get-OllamaVersion $status.exe
    }
    $proc = Get-Process | Where-Object { $_.Name -like '*ollama*' } | Select-Object -First 1
    $status.running = [bool]$proc
    $api = Get-OllamaApiTags
    $status.reachable = $api.success
    if ($api.success) {
        $status.models = $api.names
        $status.model_present = ($api.names -contains $Model) -or ($api.names -contains "$Model`:latest")
    }
    if (-not $status.installed) {
        $status.state = 'NOT_INSTALLED'
    } elseif (-not $status.reachable) {
        $status.state = 'SERVER_UNREACHABLE'
    } elseif (-not $status.model_present) {
        $status.state = 'MODEL_MISSING'
    } else {
        $status.state = 'OK'
    }
    return $status
}

function Install-OllamaWinget {
    Write-Output 'Installing Ollama via winget...'
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw 'winget is not available. Install Ollama manually from https://ollama.com/download/windows'
    }
    & winget install --id Ollama.Ollama --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) {
        throw "winget install exited with code $LASTEXITCODE. If elevation was required, run this script as Administrator or install Ollama manually from https://ollama.com/download/windows"
    }
    Write-Output 'Ollama installed. Waiting briefly for the service to start...'
    Start-Sleep -Seconds 5
}

function Start-OllamaIfInstalled {
    param($exe)
    if (-not $exe) { return $false }
    try {
        Start-Process -FilePath $exe -ArgumentList 'serve' -WindowStyle Hidden
        Start-Sleep -Seconds 3
        return $true
    } catch {
        return $false
    }
}

function Invoke-ModelPull($exe, $model) {
    Write-Output "Pulling Ollama model $model ..."
    & $exe pull $model
    if ($LASTEXITCODE -ne 0) {
        throw "ollama pull exited with code $LASTEXITCODE"
    }
}

function Write-EnvFile {
    param($path, $model, $kimiKey)
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add('OLLAMA_HOST=http://127.0.0.1:11434')
    $lines.Add("OLLAMA_LOCAL_MODEL=$model")
    if ($kimiKey) { $lines.Add("KIMI_API_KEY=$kimiKey") }
    if (Test-Path $path) {
        $existing = [System.IO.File]::ReadAllLines($path)
        foreach ($line in $existing) {
            if ($line -notmatch '^(OLLAMA_HOST|OLLAMA_LOCAL_MODEL|KIMI_API_KEY)=') {
                $lines.Add($line)
            }
        }
    }
    $unique = $lines | Select-Object -Unique
    [System.IO.File]::WriteAllLines($path, [string[]]$unique)
}

# --- Pre-checks ---
if (-not (Test-Path (Join-Path $root '.gitignore'))) {
    throw '.gitignore missing; refusing to create .env'
}
git -C $root check-ignore -q .env
if ($LASTEXITCODE -ne 0) { throw '.env is not ignored; refusing to continue' }

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
    if ($python) { $python = & py -3.12 -c 'import sys; print(sys.executable)' }
}
if (-not $python) {
    throw 'Python not found. Install Python 3.12.x and ensure python or py is on PATH.'
}
$pyVersion = & python --version 2>&1
if ($pyVersion -notmatch '3\.12') {
    Write-Warning "Python 3.12.x is recommended; found: $pyVersion"
}

# --- Ollama status ---
$status = Get-OllamaStatus

if ($CheckOnly) {
    Write-Output ($status | ConvertTo-Json)
    exit 0
}

# --- Install Ollama if requested and missing ---
if ($status.state -eq 'NOT_INSTALLED') {
    if ($InstallOllama) {
        Install-OllamaWinget
        $status = Get-OllamaStatus
    } else {
        Write-Warning "Ollama is NOT_INSTALLED. Re-run with -InstallOllama to install via winget, or install manually from https://ollama.com/download/windows"
    }
}

# --- Start Ollama if installed but unreachable ---
if ($status.installed -and -not $status.reachable) {
    if (-not (Start-OllamaIfInstalled $status.exe)) {
        Write-Warning "Ollama is installed but the server is unreachable. Ensure the Ollama app is running (it starts automatically after install)."
    }
    $status = Get-OllamaStatus
}

# --- Pull model if requested and missing ---
if ($status.state -eq 'MODEL_MISSING') {
    if ($PullModel) {
        Invoke-ModelPull $status.exe $Model
        $status = Get-OllamaStatus
    } else {
        Write-Warning "Model $Model is MODEL_MISSING. Re-run with -PullModel to download it (~2 GB), or run: ollama pull $Model"
    }
}

# --- Kimi key prompt ---
$kimiKey = $null
if (-not $SkipKimiKey) {
    $secure = Read-Host 'Kimi/Moonshot API key (leave blank to skip)' -AsSecureString
    if ($secure.Length -gt 0) {
        $kimiKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
    }
}

# --- Write .env ---
Write-EnvFile -path $envFile -model $Model -kimiKey $kimiKey
Write-Status 'ENV' 'WRITTEN' $envFile

# --- Final summary ---
Write-Status 'PYTHON' 'FOUND' $pyVersion
Write-Status 'OLLAMA' $status.state "version=$($status.version); running=$($status.running); reachable=$($status.reachable); model_present=$($status.model_present)"
Write-Status 'KIMI_KEY' $(if ($kimiKey) { 'SET' } else { 'MISSING (optional)' })

if ($status.state -ne 'OK') {
    Write-Output "`nLocal AI is not fully ready. Address the Ollama state above, then re-run."
    exit 1
}

Write-Output "`nLocal AI setup verified. Run scripts/check_dev_environment.py --ollama for a quick probe."
