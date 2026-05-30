$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$Root\scripts\start-backend.ps1`""
)

Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$Root\scripts\start-worker.ps1`""
)

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$Root\scripts\start-frontend.ps1`""
)

Write-Host "Started backend on http://127.0.0.1:8000"
Write-Host "Started frontend on http://localhost:3000"
Write-Host "Started worker in background"

