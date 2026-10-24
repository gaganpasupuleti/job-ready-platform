# Production-build smoke (vite preview). Requires backend at $ApiBase.
param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [int]$PreviewPort = 4173,
  [switch]$TestFailurePropagation
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$exitCode = 0
$previewPid = $null
$readinessMarker = $null
$markerRel = "e2e-preview-ready.txt"
$script:lastCommandExit = 0

function Invoke-Checked {
  param([string]$Label, [scriptblock]$Block)
  & $Block
  $script:lastCommandExit = $LASTEXITCODE
  if ($script:lastCommandExit -ne 0) {
    throw "$Label failed with exit code $script:lastCommandExit"
  }
}

function Assert-PreviewPortFree {
  param([int]$Port)
  $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -ne $conn) {
    throw "Preview port $Port is already in use (listener PID $($conn.OwningProcess)). Stop the stale server before running smoke."
  }
}

function Stop-PreviewTree {
  if ($null -eq $previewPid) { return }
  try {
    & taskkill.exe /PID $previewPid /T /F 2>$null | Out-Null
  } catch {
    # preview already exited
  }
  $script:previewPid = $null
}

function Wait-PreviewReady {
  param([string]$MarkerUrl, [string]$ExpectedBody, [int]$TimeoutSec = 90)
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    if ($previewPid -and (Get-Process -Id $previewPid -ErrorAction SilentlyContinue).HasExited) {
      throw "vite preview process exited before becoming ready"
    }
    try {
      $res = Invoke-WebRequest -Uri $MarkerUrl -UseBasicParsing -TimeoutSec 3
      if ($res.StatusCode -eq 200 -and $res.Content.Trim() -eq $ExpectedBody) { return }
    } catch {
      Start-Sleep -Milliseconds 500
    }
  }
  throw "Timed out waiting for preview marker at $MarkerUrl (stale server on port is not accepted)"
}

try {
  if ($TestFailurePropagation) {
    Invoke-Checked "controlled failure probe" { node -e "process.exit(42)" }
  }

  Assert-PreviewPortFree -Port $PreviewPort

  $env:VITE_API_BASE_URL = $ApiBase
  $env:VITE_ENABLE_DEV_LOGIN = "false"
  Invoke-Checked "npm run build" { npm run build }

  $readinessMarker = [guid]::NewGuid().ToString()
  $markerPath = Join-Path (Join-Path $Root "dist") $markerRel
  Set-Content -Path $markerPath -Value $readinessMarker -NoNewline -Encoding ascii

  $previewUrl = "http://127.0.0.1:$PreviewPort"
  $markerUrl = "$previewUrl/$markerRel"
  $previewProc = Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/c", "npm run preview -- --host 127.0.0.1 --port $PreviewPort --strictPort"
  ) -PassThru -WindowStyle Hidden
  $previewPid = $previewProc.Id
  Wait-PreviewReady -MarkerUrl $markerUrl -ExpectedBody $readinessMarker

  $env:E2E_BASE_URL = $previewUrl
  $env:E2E_SKIP_WEBSERVER = "1"
  $env:E2E_API_URL = $ApiBase
  $env:E2E_ALLOW_SEED = "1"

  $specs = @(
    @{ Label = "AUTH-01 (preview, registration closed path)"; Args = @("e2e/auth.spec.ts", "-g", "AUTH-01", "--project=desktop") },
    @{ Label = "More menu keyboard"; Args = @("e2e/phase5-mock.spec.ts", "-g", "More menu", "--project=desktop") },
    @{ Label = "roadmap mock UI"; Args = @("e2e/roadmap-mock.spec.ts", "--project=desktop") },
    @{ Label = "roadmap catalog live"; Args = @("e2e/roadmap-catalog-render.spec.ts", "--project=desktop") },
    @{ Label = "roadmap graph interaction"; Args = @("e2e/roadmap-graph-interaction.spec.ts", "--project=desktop") },
    @{ Label = "release preview live"; Args = @("e2e/release-smoke-preview.spec.ts", "--project=desktop") }
  )

  foreach ($spec in $specs) {
    Invoke-Checked $spec.Label { npx playwright test @($spec.Args) }
  }
} catch {
  if ($_.Exception.Message -match 'exit code (\d+)') {
    $exitCode = [int]$Matches[1]
  } elseif ($script:lastCommandExit -ne 0) {
    $exitCode = $script:lastCommandExit
  } else {
    $exitCode = 1
  }
} finally {
  Stop-PreviewTree
  if ($readinessMarker) {
    $markerPath = Join-Path (Join-Path $Root "dist") $markerRel
    if (Test-Path $markerPath) { Remove-Item $markerPath -Force -ErrorAction SilentlyContinue }
  }
}

exit $exitCode
