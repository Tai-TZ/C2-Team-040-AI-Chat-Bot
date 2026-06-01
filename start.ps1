# Chạy backend (port 8000) + frontend (port 8080) cùng lúc
$Root = $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Chua co .venv — tao virtualenv truoc:" -ForegroundColor Yellow
    Write-Host "  py -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .\.venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Chua co frontend/node_modules — chay: cd frontend && npm install" -ForegroundColor Yellow
    exit 1
}

# Neu da cai concurrently o root thi dung 1 terminal
if (Test-Path "node_modules\concurrently") {
    npm run dev
    exit $LASTEXITCODE
}

# Fallback: mo 2 cua so terminal rieng
Write-Host "Starting backend + frontend in 2 windows..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$Root'; Write-Host '=== BACKEND :8000 ===' -ForegroundColor Blue; .\.venv\Scripts\python api_server.py"
)
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$Root\frontend'; Write-Host '=== FRONTEND :8080 ===' -ForegroundColor Green; npm run dev"
)
Write-Host ""
Write-Host "Backend:  http://localhost:8000/api/health" -ForegroundColor Blue
Write-Host "Frontend: http://localhost:8080/" -ForegroundColor Green
