param([Parameter(Mandatory = $true)][string]$TunnelUrl)
$ErrorActionPreference = "Stop"
$normalized = $TunnelUrl.Trim().TrimEnd("/")
if ($normalized -notmatch '^https://[a-z0-9-]+\.trycloudflare\.com$') { throw "Use the HTTPS URL printed by cloudflared, e.g. https://example-name.trycloudflare.com" }
$root = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $root "public\config.js"
$value = 'window.ATTEND_AI_BACKEND_URL = "' + $normalized + '";'
Set-Content -Path $configPath -Value $value -Encoding utf8
Write-Host "Vercel launch portal now links to $normalized" -ForegroundColor Green
Write-Host "Commit and push public/config.js to update the Vercel static site."
