# Production-build smoke (vite preview). Requires backend at $ApiBase and E2E manifest credentials.
param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [int]$PreviewPort = 4173
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$env:VITE_API_BASE_URL = $ApiBase
$env:VITE_ENABLE_DEV_LOGIN = "false"
npm run build

$preview = Start-Process -FilePath "npm" -ArgumentList "run","preview","--","--host","127.0.0.1","--port",$PreviewPort -PassThru -NoNewWindow
Start-Sleep -Seconds 3

$env:E2E_BASE_URL = "http://127.0.0.1:$PreviewPort"
$env:E2E_SKIP_WEBSERVER = "1"
$env:E2E_API_URL = $ApiBase

try {
  npx playwright test e2e/auth.spec.ts -g "AUTH-01" --project=desktop
  npx playwright test e2e/phase5-mock.spec.ts -g "More menu" --project=desktop
  npx playwright test e2e/roadmap-mock.spec.ts --project=desktop
} finally {
  if ($preview -and -not $preview.HasExited) {
    Stop-Process -Id $preview.Id -Force -ErrorAction SilentlyContinue
  }
}
