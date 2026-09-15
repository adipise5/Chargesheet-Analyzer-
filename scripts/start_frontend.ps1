$ErrorActionPreference = 'Stop'
$repoDir = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $repoDir 'frontend')
if (-not (Test-Path 'node_modules')) { throw 'Frontend dependencies missing. Run .\scripts\setup_windows.ps1 first.' }
npm run dev
