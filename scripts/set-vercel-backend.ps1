param([Parameter(Mandatory = $true)][string]$TunnelUrl)
$ErrorActionPreference = "Stop"
$normalized = $TunnelUrl.Trim().TrimEnd("/")
if ($normalized -notmatch '^https://[a-z0-9-]+\.trycloudflare\.com$') { throw "Use the HTTPS URL printed by cloudflared, e.g. https://example-name.trycloudflare.com" }
$root = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $root "vercel.json"
$config = Get-Content $configPath -Raw
$config = $config -replace 'https://REPLACE-WITH-CLOUDFLARE-TUNNEL\.trycloudflare\.com', $normalized
$config = $config -replace 'https://[a-z0-9-]+\.trycloudflare\.com', $normalized
Set-Content -Path $configPath -Value $config -Encoding utf8
Write-Host "Vercel proxy now targets $normalized" -ForegroundColor Green
Write-Host "Commit and push vercel.json to trigger a Vercel deployment."
