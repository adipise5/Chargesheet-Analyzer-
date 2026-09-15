$ErrorActionPreference = 'Stop'
$repoDir = Split-Path -Parent $PSScriptRoot
Set-Location $repoDir
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Python environment missing. Run .\scripts\setup_windows.ps1 first.' }
& .venv\Scripts\python.exe -m pytest backend\tests
Push-Location frontend
try {
    npm run lint
    npm run build
} finally {
    Pop-Location
}
