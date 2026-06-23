param(
  [string]$DataRepoUrl = "https://github.com/subothsundar123/reddit-scraper-github-publisher.git",
  [string]$LocalDataDirectory = "$env:USERPROFILE\Documents\Nubra Product Insights"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
  Write-Host "Creating the local Python environment..."
  python -m venv (Join-Path $root ".venv")
}

& $python -m pip install --upgrade pip
& $python -m pip install -e $root

$claudeDirectory = Join-Path $env:APPDATA "Claude"
$configPath = Join-Path $claudeDirectory "claude_desktop_config.json"
New-Item -ItemType Directory -Path $claudeDirectory -Force | Out-Null

if (Test-Path -LiteralPath $configPath) {
  Write-Host "The existing Claude Desktop configuration will be backed up before merging."
}

& $python (Join-Path $PSScriptRoot "configure_claude_desktop.py") `
  --config $configPath `
  --python $python `
  --repo-url $DataRepoUrl `
  --local-data-dir $LocalDataDirectory

Write-Host ""
Write-Host "Claude Desktop connector installed successfully."
Write-Host "Configuration: $configPath"
Write-Host "Local insights folder: $LocalDataDirectory"
Write-Host ""
Write-Host "Completely quit and reopen Claude Desktop."
Write-Host "In a new chat, click + > Connectors and confirm 'reddit-product-insights' is connected."
Write-Host "Then type: Give me today's daily product insights."
