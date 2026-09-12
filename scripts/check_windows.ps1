$ErrorActionPreference = 'Stop'

$repoDir = Split-Path -Parent $PSScriptRoot
Set-Location $repoDir

if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Python environment missing. Run .\scripts\setup_windows.ps1 first.' }
if (-not (Test-Path 'frontend\node_modules')) { throw 'Frontend dependencies missing. Run .\scripts\setup_windows.ps1 first.' }

& .venv\Scripts\python.exe --version
node --version
npm --version

if (Get-Command tesseract -ErrorAction SilentlyContinue) {
    $languages = & tesseract --list-langs 2>$null
    if ($languages -match '^guj$' -and $languages -match '^eng$') {
        Write-Host 'Tesseract Gujarati and English language data: ready'
    } else {
        Write-Warning 'Tesseract is installed but guj and/or eng language data is missing.'
    }
} else {
    Write-Warning 'Tesseract is not installed. Native-text PDFs still work; scanned PDFs require Tesseract.'
}

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    try { & ollama list } catch { Write-Warning 'Ollama is installed but not running.' }
} else {
    Write-Warning 'Ollama is not installed. The synthetic demo and extractive Q&A still work.'
}

Write-Host 'System check complete.'
