# setup_atlas.ps1
# Sets up the ATLAS AI Orchestration project

Write-Host "🚀 Setting up ATLAS AI Orchestration Project..." -ForegroundColor Cyan

# 1. Create a root .env if it doesn't exist
# 2. Sync .env to services for local development
Copy-Item .env services\orchestrator\.env -Force
Copy-Item .env services\google-mcp\.env -Force
Copy-Item .env apps\web-console\.env -Force

Write-Host "✅ Environment files synced." -ForegroundColor Green

# 3. Check for credentials.json
if (-Not (Test-Path "services\google-mcp\credentials.json")) {
    Write-Host "⚠️ Warning: services\google-mcp\credentials.json missing!" -ForegroundColor Yellow
} else {
    Write-Host "✅ credentials.json found." -ForegroundColor Green
}

Write-Host "`nTo run the project, use:" -ForegroundColor Cyan
Write-Host "docker-compose up --build" -ForegroundColor White
Write-Host "`nOr run services individually:" -ForegroundColor Cyan
Write-Host "1. Orchestrator: cd services/orchestrator; uvicorn app.main:app --port 9000"
Write-Host "2. Google MCP:   cd services/google-mcp; uvicorn backend.main:app --port 8000"
Write-Host "3. Web Console:  cd apps/web-console; pnpm dev"
