$ErrorActionPreference = 'Stop'
$repoDir = Split-Path -Parent $PSScriptRoot

$backend = Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -PassThru -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'start_backend.ps1'))
$frontend = Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -PassThru -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'start_frontend.ps1'))
Write-Host 'Backend:  http://127.0.0.1:8000/docs'
Write-Host 'Frontend: http://127.0.0.1:5173'
Write-Host 'Press Ctrl+C to stop both services.'

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    $backend, $frontend | Where-Object { -not $_.HasExited } | Stop-Process -Force
}
