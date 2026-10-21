# Copy Power BI PDF export from Downloads into public/reports for in-app preview.
$destDir = Join-Path $PSScriptRoot "..\public\reports"
$names = @(
  "executive-sales-toast.pdf",
  "Exceutive Sales Report - Toast Notifictaion.pdf"
)
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
foreach ($name in $names) {
  $src = Join-Path (Join-Path $env:USERPROFILE "Downloads") $name
  if (-not (Test-Path -LiteralPath $src)) { continue }
  $dest = Join-Path $destDir $name
  Copy-Item -LiteralPath $src -Destination $dest -Force
  Write-Host "Copied $name -> public/reports/"
  exit 0
}
Write-Host "No PDF found in Downloads. Export from Power BI Desktop first (File -> Export -> PDF)."
exit 1
