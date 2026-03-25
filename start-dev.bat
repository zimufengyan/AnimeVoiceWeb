@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

set "FRONTEND_DIR=%ROOT_DIR%\AnimeSpeechGen"
set "BACKEND_DIR=%ROOT_DIR%\AniVoiceBackend"
set "ROOT_ENV=%ROOT_DIR%\.env"
set "BACKEND_ENV=%BACKEND_DIR%\.env"

set "BACKEND_ENTRY=app.py"
set "CONDA_ENV=web"
set "POSTGRES_SERVICE_NAME="
set "SKIP_POSTGRES="

if /I "%~1"=="-SkipPostgres" set "SKIP_POSTGRES=1"

call :load_env "%ROOT_ENV%"
call :load_env "%BACKEND_ENV%"

if not exist "%FRONTEND_DIR%" (
    echo Frontend directory not found: %FRONTEND_DIR%
    exit /b 1
)

if not exist "%BACKEND_DIR%" (
    echo Backend directory not found: %BACKEND_DIR%
    exit /b 1
)

if not exist "%BACKEND_DIR%\%BACKEND_ENTRY%" (
    echo Backend entry not found: %BACKEND_DIR%\%BACKEND_ENTRY%
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    echo Node.js was not found in PATH.
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo npm was not found in PATH.
    exit /b 1
)

where conda >nul 2>nul
if errorlevel 1 (
    echo conda was not found in PATH.
    exit /b 1
)

echo Frontend directory: %FRONTEND_DIR%
echo Backend directory:  %BACKEND_DIR%
echo Backend entry:      %BACKEND_ENTRY%
echo Conda environment:  %CONDA_ENV%
echo.

if not defined SKIP_POSTGRES (
    call :start_postgres
    echo.
)

echo Starting frontend in a new terminal window...
start "AnimeSpeechGen Frontend" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev"

echo Starting backend in a new terminal window...
start "AnimeSpeechGen Backend" cmd /k "cd /d ""%BACKEND_DIR%"" && conda run -n %CONDA_ENV% python %BACKEND_ENTRY%"

echo.
echo Both start commands have been launched.
exit /b 0

:load_env
set "ENV_FILE=%~1"
if not exist "%ENV_FILE%" goto :eof

for /f "usebackq tokens=* delims=" %%L in ("%ENV_FILE%") do (
    set "LINE=%%L"
    if defined LINE (
        if not "!LINE:~0,1!"=="#" (
            for /f "tokens=1* delims==" %%A in ("!LINE!") do (
                if not "%%A"=="" (
                    set "%%A=%%B"
                )
            )
        )
    )
)
goto :eof

:start_postgres
if not defined POSTGRES_SERVICE_NAME (
    echo POSTGRES_SERVICE_NAME is not configured. Skipping PostgreSQL startup.
    goto :eof
)

sc query "%POSTGRES_SERVICE_NAME%" | find "RUNNING" >nul
if not errorlevel 1 (
    echo PostgreSQL service is already running: %POSTGRES_SERVICE_NAME%
    goto :eof
)

echo Starting PostgreSQL service: %POSTGRES_SERVICE_NAME%
net start "%POSTGRES_SERVICE_NAME%"
if errorlevel 1 (
    echo Failed to start PostgreSQL service: %POSTGRES_SERVICE_NAME%
)
goto :eof
