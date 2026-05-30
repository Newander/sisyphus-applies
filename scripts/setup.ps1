# First-time setup: installs dependencies, applies migrations, and starts the app.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Write-Step  { param($msg) Write-Host "`n==> $msg" -ForegroundColor Blue }
function Write-Ok    { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Fail  { param($msg) Write-Host $msg -ForegroundColor Red }

# ── Prerequisites ─────────────────────────────────────────────────────────────
Write-Step "Checking prerequisites"

try {
    $pyVer = python --version 2>&1
    $pyNum = ($pyVer -replace "Python ","").Split(".")
    if ([int]$pyNum[0] -lt 3 -or ([int]$pyNum[0] -eq 3 -and [int]$pyNum[1] -lt 12)) {
        Write-Fail "Python 3.12+ is required (found $pyVer)."; exit 1
    }
    Write-Ok "$pyVer ✓"
} catch {
    Write-Fail "Python 3.12+ is required but not found."; exit 1
}

try {
    $nodeVer = node --version 2>&1
    Write-Ok "Node.js $nodeVer ✓"
} catch {
    Write-Fail "Node.js 18+ is required but not found."; exit 1
}

# ── .env ──────────────────────────────────────────────────────────────────────
Write-Step "Configuring environment"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Warn ".env created from .env.example."
    Write-Warn "Default credentials: postgres/postgres on localhost:5432."
    Write-Warn "Edit .env if your PostgreSQL setup differs, then re-run this script."
    Read-Host "`nPress Enter to continue with the defaults, or Ctrl+C to edit .env first"
} else {
    Write-Ok ".env already exists ✓"
}

# ── Backend ───────────────────────────────────────────────────────────────────
Write-Step "Installing backend dependencies"
& "$Root\scripts\install-backend.ps1"
Write-Ok "Backend dependencies installed ✓"

# ── Frontend ──────────────────────────────────────────────────────────────────
Write-Step "Installing frontend dependencies"
& "$Root\scripts\install-frontend.ps1"
Write-Ok "Frontend dependencies installed ✓"

# ── Database ──────────────────────────────────────────────────────────────────
Write-Step "Applying database migrations"
& "$Root\scripts\init-db.ps1"
Write-Ok "Migrations applied ✓"

# ── Seed data ─────────────────────────────────────────────────────────────────
$seed = Read-Host "`nSeed the database with demo data? [y/N]"
if ($seed -match "^[Yy]$") {
    Write-Step "Seeding demo data"
    & "$Root\scripts\seed-data.ps1"
    Write-Ok "Demo data loaded ✓"
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host "`n Setup complete." -ForegroundColor Green
Write-Host ""
Write-Host "Start the app:"
Write-Host "  .\scripts\start-all.ps1"
Write-Host ""
Write-Host "  Frontend -> http://localhost:9001"
Write-Host "  Backend  -> http://127.0.0.1:9002"
Write-Host ""
