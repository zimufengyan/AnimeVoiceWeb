param(
    [string]$BackendEntry = "app.py",
    [switch]$SameWindow
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $RootDir "AnimeSpeechGen"
$BackendDir = Join-Path $RootDir "AniVoiceBackend"

function Test-CommandExists {
    param([string]$Name)

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Assert-PathExists {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        throw "$Label not found: $Path"
    }
}

Assert-PathExists -Path $FrontendDir -Label "Frontend directory"
Assert-PathExists -Path $BackendDir -Label "Backend directory"

if (-not (Test-CommandExists "node")) {
    throw "Node.js was not found in PATH."
}

if (-not (Test-CommandExists "npm")) {
    throw "npm was not found in PATH."
}

if (-not (Test-CommandExists "python")) {
    throw "Python was not found in PATH."
}

$BackendScript = Join-Path $BackendDir $BackendEntry
Assert-PathExists -Path $BackendScript -Label "Backend entry"

Write-Host "Frontend directory: $FrontendDir"
Write-Host "Backend directory:  $BackendDir"
Write-Host "Backend entry:      $BackendEntry"
Write-Host ""

if ($SameWindow) {
    Write-Host "Starting frontend in the current window..."
    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$FrontendDir'; npm run dev"
    )

    Write-Host "Starting backend in the current window..."
    Set-Location $BackendDir
    python $BackendEntry
    exit $LASTEXITCODE
}

Write-Host "Starting frontend in a new terminal window..."
Start-Process -FilePath "powershell.exe" -WorkingDirectory $FrontendDir -ArgumentList @(
    "-NoExit",
    "-Command",
    "npm run dev"
)

Write-Host "Starting backend in a new terminal window..."
Start-Process -FilePath "powershell.exe" -WorkingDirectory $BackendDir -ArgumentList @(
    "-NoExit",
    "-Command",
    "python $BackendEntry"
)

Write-Host ""
Write-Host "Both start commands have been launched."
Write-Host "If the backend entry needs to change, run:"
Write-Host ".\start-dev.ps1 -BackendEntry app_fast.py"
