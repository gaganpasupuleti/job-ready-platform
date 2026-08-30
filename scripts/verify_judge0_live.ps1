# Requires: JUDGE0_URL, JUDGE0_AUTH_TOKEN in environment (or pass as params)
param(
    [string]$Judge0Url = $env:JUDGE0_URL,
    [string]$AuthToken = $env:JUDGE0_AUTH_TOKEN,
    [string]$AuthHeader = $(if ($env:JUDGE0_AUTH_HEADER) { $env:JUDGE0_AUTH_HEADER } else { "X-Auth-Token" })
)

$ErrorActionPreference = "Stop"

if (-not $Judge0Url -or -not $AuthToken) {
    Write-Error "Set JUDGE0_URL and JUDGE0_AUTH_TOKEN (or pass -Judge0Url / -AuthToken)."
}

$repoRoot = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $repoRoot "backend"
if (-not (Test-Path (Join-Path $backend "tests\test_judge0_live.py"))) {
    Write-Error "Could not find backend/tests/test_judge0_live.py from $repoRoot"
}
Set-Location $backend

$env:JUDGE0_LIVE_TESTS = "1"
$env:JUDGE0_ENABLED = "true"
$env:JUDGE0_URL = $Judge0Url.TrimEnd("/")
$env:JUDGE0_AUTH_HEADER = $AuthHeader
$env:JUDGE0_AUTH_TOKEN = $AuthToken

Write-Host "Health: $env:JUDGE0_URL/about"
try {
    Invoke-RestMethod -Uri "$env:JUDGE0_URL/about" -Headers @{ $AuthHeader = $AuthToken } | Out-Null
    Write-Host "Judge0 /about OK"
} catch {
    Write-Warning "Health check failed (continuing to pytest): $_"
}

Write-Host "Running tests/test_judge0_live.py ..."
python -m pytest tests/test_judge0_live.py -q --tb=short
exit $LASTEXITCODE
