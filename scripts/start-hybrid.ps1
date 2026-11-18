$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python environment missing. Create .venv with Python 3.11 and install requirements.txt." }
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) { throw "Install Cloudflare Tunnel: winget install --id Cloudflare.cloudflared" }
if (-not (Test-Path (Join-Path $root ".env"))) { throw ".env is missing. Copy .env.example to .env and configure secrets first." }
$env:COOKIE_SECURE = "true"
$server = Start-Process -FilePath $python -ArgumentList "app.py" -WorkingDirectory $root -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $root "backend.log") -RedirectStandardError (Join-Path $root "backend-error.log")
try {
    Start-Sleep -Seconds 4
    if ($server.HasExited) { Get-Content (Join-Path $root "backend-error.log") -ErrorAction SilentlyContinue; throw "Flask did not start. Check backend-error.log." }
    Write-Host "AttendAI backend is running at http://127.0.0.1:5000" -ForegroundColor Green
    Write-Host "Keep this window open. Copy the HTTPS trycloudflare.com URL printed below." -ForegroundColor Yellow
    & cloudflared tunnel --url http://127.0.0.1:5000
}
finally {
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
}
