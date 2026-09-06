param([string]$Model = "llama3.2:3b")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $root '.env'
$key = Read-Host 'Kimi/Moonshot API key (leave blank to skip)' -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($key))
try {
  $lines = @('OLLAMA_HOST=http://127.0.0.1:11434', "OLLAMA_LOCAL_MODEL=$Model")
  if ($plain) { $lines += "KIMI_API_KEY=$plain" }
  Set-Content -LiteralPath $envFile -Value $lines -Encoding utf8
  git -C $root check-ignore -q .env
  if ($LASTEXITCODE -ne 0) { throw '.env is not ignored; refusing to continue' }
  Write-Output ('KIMI credential ' + $(if($plain){'SET'}else{'MISSING'}))
  Write-Output 'OLLAMA host SET'; Write-Output ('OLLAMA model ' + $Model)
} finally { $plain = $null }
