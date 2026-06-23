param(
  [string]$DataRepoUrl = "https://github.com/subothsundar123/reddit-scraper-github-publisher.git",
  [string]$LocalDataDirectory = "$env:USERPROFILE\Documents\Nubra Product Insights"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
  throw "Agent environment not found. Run scripts\install.ps1 first."
}

$env:INSIGHTS_DATA_REPO_URL = $DataRepoUrl
$env:INSIGHTS_DATA_BRANCH = "main"
$env:INSIGHTS_LOCAL_DATA_DIR = $LocalDataDirectory
$env:INSIGHTS_DESKTOP_LOCAL_ONLY = "0"
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "Never"

Write-Host "Updating Reddit Product Insights data..."
& $python -m reddit_insights_agent.cli sync
if ($LASTEXITCODE -ne 0) {
  throw "Data update failed. Confirm GitHub authentication and repository access."
}

$statePath = Join-Path $LocalDataDirectory "sync-state.json"
if (-not (Test-Path -LiteralPath $statePath)) {
  throw "Sync completed without creating state: $statePath"
}

$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
$latest = $state.dumps | Sort-Object | Select-Object -Last 1
Write-Host ""
Write-Host "Local insights data is ready."
Write-Host "Latest dump: $latest"
Write-Host "Catalog version: $($state.catalog_version)"
Write-Host "Folder: $LocalDataDirectory"

