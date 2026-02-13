# Start app with reload, wait, then run API tests.
# Usage: .\scripts\run_tests.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

# Start uvicorn in background with reload so code changes are picked up
$job = Start-Job -ScriptBlock {
    Set-Location $using:root
    & .\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
}
Start-Sleep -Seconds 8
try {
    & .\.venv\Scripts\python.exe scripts/test_api.py
} finally {
    Stop-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -Force -ErrorAction SilentlyContinue
}
