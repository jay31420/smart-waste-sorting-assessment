$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceDir = Split-Path -Parent $projectDir
Set-Location $projectDir

$bridge = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" |
    Where-Object { $_.CommandLine -match 'host_camera_bridge.py' } |
    Select-Object -First 1

if (-not $bridge) {
    $pythonCandidates = @(
        (Join-Path $workspaceDir ".venv-smart-waste-preview\Scripts\python.exe"),
        (Join-Path $projectDir ".venv\Scripts\python.exe")
    )
    $python = $pythonCandidates |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1
    if (-not $python) {
        $python = (Get-Command python -ErrorAction Stop).Source
    }
    $tempDir = Join-Path $projectDir ".codex-build\preview-temp"
    New-Item -ItemType Directory -Force $tempDir | Out-Null
    $env:TEMP = $tempDir
    $env:TMP = $tempDir
    Start-Process `
        -FilePath $python `
        -ArgumentList @(
            "tools\host_camera_bridge.py",
            "--host", "0.0.0.0",
            "--port", "8091",
            "--camera-index", "0"
        ) `
        -WorkingDirectory $projectDir `
        -WindowStyle Hidden | Out-Null
}

$cameraReady = $false
for ($attempt = 0; $attempt -lt 20; $attempt += 1) {
    try {
        $health = Invoke-RestMethod "http://127.0.0.1:8091/health" -TimeoutSec 2
        if ($health.ready) {
            $cameraReady = $true
            break
        }
    } catch {
    }
    Start-Sleep -Milliseconds 500
}

if (-not $cameraReady) {
    Write-Warning "Camera bridge is not ready. Docker will still start."
}

docker compose up --build -d
$demoUrl = "http://localhost:6080/vnc.html?autoconnect=1" + [char]38 + "resize=scale"
Start-Process $demoUrl
Write-Host "Demo environment started."
