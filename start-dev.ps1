param(
    [string]$BackendEntry = "app_fast.py",
    [string]$CondaEnv = "web",
    [switch]$SameWindow,
    [switch]$SkipPostgres
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $RootDir "AnimeSpeechGen"
$BackendDir = Join-Path $RootDir "AniVoiceBackend"
$BackendEnvFile = Join-Path $BackendDir ".env"
$RootEnvFile = Join-Path $RootDir ".env"

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

function Import-EnvFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    Write-Host "Loading env file: $Path"
    foreach ($line in Get-Content -Path $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $pair = $trimmed -split "=", 2
        if ($pair.Count -ne 2) {
            continue
        }

        $name = $pair[0].Trim()
        $value = $pair[1].Trim()

        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Get-PostgresServiceCandidate {
    param([string]$ConfiguredName)

    if ($ConfiguredName) {
        return Get-Service -Name $ConfiguredName -ErrorAction SilentlyContinue
    }

    $services = @(Get-Service -Name "postgres*" -ErrorAction SilentlyContinue)
    if ($services.Count -gt 0) {
        return $services[0]
    }

    return $null
}

function Start-PostgresIfNeeded {
    $serviceName = $env:POSTGRES_SERVICE_NAME
    $binDir = $env:POSTGRES_BIN_DIR
    $dataDir = $env:POSTGRES_DATA_DIR

    $service = Get-PostgresServiceCandidate -ConfiguredName $serviceName
    if ($service) {
        if ($service.Status -eq "Running") {
            Write-Host "PostgreSQL service is already running: $($service.Name)"
            return
        }

        Write-Host "Starting PostgreSQL service: $($service.Name)"
        try {
            Start-Service -Name $service.Name
            $service.WaitForStatus("Running", (New-TimeSpan -Seconds 15))
            Write-Host "PostgreSQL service started."
            return
        } catch {
            Write-Warning "Failed to start PostgreSQL service '$($service.Name)': $($_.Exception.Message)"
        }
    }

    $pgCtlPath = if ($binDir) {
        Join-Path $binDir "pg_ctl.exe"
    } else {
        $cmd = Get-Command "pg_ctl.exe" -ErrorAction SilentlyContinue
        if ($cmd) { $cmd.Source } else { $null }
    }

    if ($pgCtlPath -and $dataDir) {
        Write-Host "Starting PostgreSQL with pg_ctl: $pgCtlPath"
        & $pgCtlPath -D $dataDir start
        return
    }

    Write-Warning "PostgreSQL was not auto-started. Set POSTGRES_SERVICE_NAME or POSTGRES_BIN_DIR + POSTGRES_DATA_DIR in .env if you want one-click startup to manage it."
}

Assert-PathExists -Path $FrontendDir -Label "Frontend directory"
Assert-PathExists -Path $BackendDir -Label "Backend directory"

Import-EnvFile -Path $RootEnvFile
Import-EnvFile -Path $BackendEnvFile

if (-not (Test-CommandExists "node")) {
    throw "Node.js was not found in PATH."
}

if (-not (Test-CommandExists "npm")) {
    throw "npm was not found in PATH."
}

if (-not (Test-CommandExists "python")) {
    throw "Python was not found in PATH."
}

$HasConda = Test-CommandExists "conda"

$BackendScript = Join-Path $BackendDir $BackendEntry
Assert-PathExists -Path $BackendScript -Label "Backend entry"

$BackendCommand = if ($HasConda -and $CondaEnv) {
    "conda run -n $CondaEnv python $BackendEntry"
} else {
    "python $BackendEntry"
}

Write-Host "Frontend directory: $FrontendDir"
Write-Host "Backend directory:  $BackendDir"
Write-Host "Backend entry:      $BackendEntry"
if ($HasConda -and $CondaEnv) {
    Write-Host "Conda environment:  $CondaEnv"
}
Write-Host ""

if (-not $SkipPostgres) {
    Start-PostgresIfNeeded
    Write-Host ""
}

if ($SameWindow) {
    Write-Host "Starting frontend in the current window..."
    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$FrontendDir'; npm run dev"
    )

    Write-Host "Starting backend in the current window..."
    Set-Location $BackendDir
    Invoke-Expression $BackendCommand
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
    $BackendCommand
)

Write-Host ""
Write-Host "Both start commands have been launched."
Write-Host "If the backend entry needs to change, run:"
Write-Host ".\start-dev.ps1 -BackendEntry app_fast.py"
