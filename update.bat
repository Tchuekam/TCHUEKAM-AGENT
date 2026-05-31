@echo off
:: ============================================================================
:: TCHUEKAM® SOVEREIGN PLATFORM — AUTOMATED SYSTEM UPDATER
:: Developer: TCHUEKAM Loic Rostand / GIANTECT EMPIRE
:: ============================================================================

echo ====================================================================
echo  ████████╗ ██████╗██╗  ██╗██╗   ██╗██╔════╝██╗  ██╗ █████╗ ███╗   ███╗
echo  ╚══██╔══╝██╔════╝██║  ██║██║   ██║█████╗  ███████║██╔══██╗████╗ ████║
echo     ██║   ██║     ███████║██║   ██║██╔══╝  ██╔══██║███████║██╔████╔██║
echo     ██║   ╚██████╗██║  ██║╚██████╔╝███████╗██║  ██╗██║  ██║██║ ╚═╝ ██║
echo  ====================================================================
echo    [SOVEREIGN ENGINE UPDATER] [GIANTECT EMPIRE] [Yaounde, Cameroon]
echo  ====================================================================
echo.

:: Step 1: Pull changes from secure GitHub repository
echo [+] Fetching latest changes from secure Giantect Empire repository...
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] ERROR: Git pull failed. Please check host network connectivity.
    pause
    exit /b 1
)
echo [✓] Codebase pulled and merged.
echo.

:: Step 2: Synchronize local virtual environment packages
echo [+] Synchronizing local virtual environment dependencies...
cd tchuekam-agent\app
call .\venv\Scripts\activate.bat
uv sync
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] WARNING: Local dependency sync failed. Attempting force sync...
    pip install uv
    uv sync
)
echo [✓] Dependencies fully synchronized.
echo.

:: Step 3: Re-obfuscate and compile core protected binary
echo [+] Compiling protected TCHUEKAM Sovereign Engine binary...
pip install pyarmor
pyarmor pack -e " --onedir" cli.py
if %ERRORLEVEL% NEQ 0 (
    echo [!] Compiling via fallback Nuitka compiler...
    pip install nuitka
    python -m nuitka --standalone --mingw64 cli.py
)
echo [✓] Core engine compilation successfully secured.
echo.

:: Step 4: Refreshing workspace distribution pointers
echo [+] Updating operational directories...
if exist "dist\cli" (
    if exist "..\..\TchuEkamUI\resources" (
        echo Copying secure binaries to desktop runtime directory...
        xcopy /E /Y /I "dist\cli" "..\..\TchuEkamUI\resources\bundled-engine"
    )
)
echo [✓] System convergence finished.
echo.
echo ====================================================================
echo  TCHUEKAM Sovereign Engine has been fully updated and secured.
echo  Restart your TchuekamUI client to run the latest updates.
echo ====================================================================
pause
