$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "frontend")

if (-not $env:NEXT_PUBLIC_API_BASE_URL) {
    $env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:9002"
}

npm run dev -- --port 9001

