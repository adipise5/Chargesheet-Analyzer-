$ErrorActionPreference = 'Stop'
$repoDir = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $repoDir 'backend')
$python = Join-Path $repoDir '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Python environment missing. Run .\scripts\setup_windows.ps1 first.' }
$port = if ($env:APP_PORT) { $env:APP_PORT } else { '8000' }
& $python -m uvicorn app.main:app --host 127.0.0.1 --port $port --reload
