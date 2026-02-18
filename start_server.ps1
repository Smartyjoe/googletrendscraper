# ============================================================================
# PyTrends API - Server Startup Script
# ============================================================================
# This script activates the virtual environment and starts the API server
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PyTrends API - Starting Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created!" -ForegroundColor Green
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Check if dependencies are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$fastapi = pip list 2>$null | Select-String "fastapi"
if (-not $fastapi) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed!" -ForegroundColor Green
}
Write-Host ""

# Set API key if not set
if (-not $env:API_SECRET_KEY) {
    Write-Host "Setting test API key..." -ForegroundColor Yellow
    $env:API_SECRET_KEY = "test-secret-key-for-local-development-12345"
    Write-Host "✅ API key set: $env:API_SECRET_KEY" -ForegroundColor Green
} else {
    Write-Host "✅ API key already set: $env:API_SECRET_KEY" -ForegroundColor Green
}
Write-Host ""

# Start server
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting PyTrends API Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server will be available at:" -ForegroundColor Yellow
Write-Host "  → http://localhost:8000" -ForegroundColor White
Write-Host "  → http://localhost:8000/docs (API Documentation)" -ForegroundColor White
Write-Host ""
Write-Host "API Key for testing:" -ForegroundColor Yellow
Write-Host "  → $env:API_SECRET_KEY" -ForegroundColor White
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start the server
python pytrends_api.py