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
$script:lastCommandExit = 0

function Invoke-Checked {
  param([string]$Label, [scriptblock]$Block)
  & $Block
  $script:lastCommandExit = $LASTEXITCODE
  if ($script:lastCommandExit -ne 0) {
    throw "$Label failed with exit code $script:lastCommandExit"
  }
}

function Stop-PreviewTree {
  if ($null -eq $previewPid) { return }
  try {
    Stop-Process -Id $previewPid -Force -ErrorAction SilentlyContinue
  } catch {
    # preview already exited
  }
  $previewPid = $null
}

function Wait-PreviewReady {
  param([string]$Url, [int]$TimeoutSec = 60)
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    if ($previewPid -and (Get-Process -Id $previewPid -ErrorAction SilentlyContinue).HasExited) {
      throw "vite preview process exited before becoming ready"
    }
    try {
      $res = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
      if ($res.StatusCode -ge 200 -and $res.StatusCode -lt 500) { return }
    } catch {
      Start-Sleep -Milliseconds 500
    }
  }
  throw "Timed out waiting for preview at $Url"
}

try {
  if ($TestFailurePropagation) {
    Invoke-Checked "controlled failure probe" { node -e "process.exit(42)" }
  }

  $env:VITE_API_BASE_URL = $ApiBase
  $env:VITE_ENABLE_DEV_LOGIN = "false"
  Invoke-Checked "npm run build" { npm run build }

  $previewUrl = "http://127.0.0.1:$PreviewPort"
  $previewProc = Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/c", "npm run preview -- --host 127.0.0.1 --port $PreviewPort --strictPort"
  ) -PassThru -WindowStyle Hidden
  $previewPid = $previewProc.Id
  Wait-PreviewReady -Url $previewUrl

  $env:E2E_BASE_URL = $previewUrl
  $env:E2E_SKIP_WEBSERVER = "1"
  $env:E2E_API_URL = $ApiBase

  $specs = @(
    @{ Label = "AUTH-01"; Args = @("e2e/auth.spec.ts", "-g", "AUTH-01", "--project=desktop") },
    @{ Label = "More menu keyboard"; Args = @("e2e/phase5-mock.spec.ts", "-g", "More menu", "--project=desktop") },
    @{ Label = "roadmap mock UI"; Args = @("e2e/roadmap-mock.spec.ts", "--project=desktop") },
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
}

exit $exitCode
