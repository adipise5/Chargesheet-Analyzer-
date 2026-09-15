# Requires PowerShell 5.1+ and Python 3.11+ (via the Windows Python launcher).
$ErrorActionPreference = 'Stop'

$repoDir = Split-Path -Parent $PSScriptRoot
Set-Location $repoDir

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw 'Python Launcher (py.exe) is required. Install Python 3.11 or newer from python.org, then rerun.'
}

$pythonVersionText = & py -3 --version 2>&1
if ($LASTEXITCODE -ne 0 -or $pythonVersionText -notmatch 'Python\s+(\d+)\.(\d+)') {
    throw 'Python 3.11 or newer is required. Install it, then rerun this script.'
}
$pythonMajor = [int]$Matches[1]
$pythonMinor = [int]$Matches[2]
if (($pythonMajor -lt 3) -or ($pythonMajor -eq 3 -and $pythonMinor -lt 11)) {
    throw "Python 3.11 or newer is required; detected $pythonVersionText."
}

$pythonCommand = @('py', '-3')

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    & $pythonCommand[0] $pythonCommand[1] -m venv .venv
}

& .venv\Scripts\python.exe -m pip install --upgrade pip
& .venv\Scripts\python.exe -m pip install -r backend\requirements.txt

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'Node.js and npm are required. Install Node.js 20 or newer, then rerun.'
}
Push-Location frontend
try {
    npm install
} finally {
    Pop-Location
}

Write-Host 'Setup complete. Run: .\scripts\check_windows.ps1'
