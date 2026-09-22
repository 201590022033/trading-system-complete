$envFile = Join-Path $PSScriptRoot "..\.env.local"

if (-not (Test-Path $envFile)) {
    throw ".env.local not found"
}

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()

    if ($line -and -not $line.StartsWith("#")) {
        $name, $value = $line -split "=", 2

        if ($name -and $value) {
            [Environment]::SetEnvironmentVariable(
                $name.Trim(),
                $value.Trim(),
                "Process"
            )
        }
    }
}

$env:APP_MODE = "SHADOW"
$env:PORT = "5000"
$env:WORKER_ID = "local-preflight"
$env:COMMIT_SHA = (git rev-parse HEAD).Trim()

try {
    $databaseUri = [Uri]$env:DATABASE_URL
} catch {
    throw "DATABASE_URL in .env.local is not a valid URL"
}
if ($databaseUri.Scheme -notin @("postgres", "postgresql")) {
    throw "Local development requires a PostgreSQL DATABASE_URL"
}
if ($databaseUri.Host -notin @("localhost", "127.0.0.1", "::1")) {
    throw "Refusing to use a non-local PostgreSQL host for local development"
}

Write-Host "Local trading environment loaded"
Write-Host "APP_MODE=$env:APP_MODE"
Write-Host "PORT=$env:PORT"
Write-Host "COMMIT_SHA=$($env:COMMIT_SHA.Substring(0,7))"
Write-Host "WORKER_ID=$env:WORKER_ID"
Write-Host "DATABASE_URL=SET"
