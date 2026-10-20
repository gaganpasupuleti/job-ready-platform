# Regenerate Power BI lab assets (run from repository root OR frontend — paths are resolved).
$ErrorActionPreference = "Stop"
$Frontend = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $Frontend
$Pbix = Join-Path $Frontend "public/reports/Exceutive Sales Report - Toast Notifictaion.pbix"
$Preview = Join-Path $Frontend "public/reports/executive-sales-toast.png"
$Out = Join-Path $Frontend "public/reports/executive-sales-toast-lab"

if (-not (Test-Path $Pbix)) { throw "Missing PBIX: $Pbix" }

Write-Host "1/5 extract-pbix-lab (CSVs, crops, dax; does NOT touch workshop-content.json)"
python (Join-Path $Frontend "scripts/extract-pbix-lab.py") --pbix $Pbix --out $Out --preview $Preview

Write-Host "2/5 compute expected-results.json"
python (Join-Path $Frontend "scripts/compute-expected-results.py")

Write-Host "3/5 csv import M snippets"
python (Join-Path $Frontend "scripts/generate-csv-import-queries.py")

Write-Host "4/5 workshop content + student kit + build-guide.md"
python (Join-Path $Frontend "scripts/build-executive-sales-workshop.py")

Write-Host "5/6 screenshot audit metadata"
python (Join-Path $Frontend "scripts/audit-lab-screenshots.py")

Write-Host "6/6 validate"
Set-Location $Frontend
npm run validate:power-bi-lab
Write-Host "Done. Lab output: $Out"
