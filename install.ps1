# LifeClaw — Windows Installer (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host @"
  _     _  __       ____ _
 | |   (_)/ _| ___ / ___| | __ ___      __
 | |   | | |_ / _ \ |   | |/ _`` \ \ /\ / /
 | |___| |  _|  __/ |___| | (_| |\ V  V /
 |_____|_|_|  \___|\____|_|\__,_| \_/\_/

"@ -ForegroundColor Cyan

Write-Host "LifeClaw Installer" -ForegroundColor White
Write-Host ""

# Check Python
try {
    $pyVer = python --version 2>&1
    Write-Host "[OK] $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[X] Python 3.11+ required. Install from https://python.org" -ForegroundColor Red
    exit 1
}

# Check Node
try {
    $nodeVer = node --version 2>&1
    Write-Host "[OK] Node.js $nodeVer" -ForegroundColor Green
    $hasNode = $true
} catch {
    Write-Host "[!] Node.js not found (web dashboard won't be available)" -ForegroundColor Yellow
    $hasNode = $false
}

# Check Ollama
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction SilentlyContinue
    Write-Host "[OK] Ollama detected" -ForegroundColor Green
} catch {
    Write-Host "[!] Ollama not found. Install at https://ollama.ai" -ForegroundColor Yellow
}

Write-Host ""

# Clone or update
$installDir = "$env:USERPROFILE\LifeClaw"
if (Test-Path $installDir) {
    Write-Host "Updating existing installation..." -ForegroundColor Cyan
    Set-Location $installDir
    git pull --quiet origin main 2>$null
} else {
    Write-Host "Cloning LifeClaw..." -ForegroundColor Cyan
    git clone --quiet https://github.com/slashdoodleart/LifeClaw.git $installDir
    Set-Location $installDir
}

# Install
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
pip install -e . --quiet

if ($hasNode) {
    Write-Host "Installing web dashboard..." -ForegroundColor Cyan
    Set-Location web
    npm install --silent 2>$null
    Set-Location ..
}

Write-Host ""
Write-Host "[OK] LifeClaw installed!" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "  lifeclaw setup    - Interactive setup" -ForegroundColor Cyan
Write-Host "  lifeclaw chat     - Start chatting" -ForegroundColor Cyan
Write-Host "  lifeclaw chat -c  - Coder mode" -ForegroundColor Cyan
Write-Host ""
