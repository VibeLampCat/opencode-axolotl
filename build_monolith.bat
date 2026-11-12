@echo off
setlocal enabledelayedexpansion
title OpenCode v2.2.7 + ArgonBug Monolithic Build Pipeline

echo ========================================================
echo  OpenCode v2.2.7 + ArgonBug Monolithic Build Pipeline
echo ========================================================
echo.

:: 1. Auto-detect Bun in standard paths if not yet in PATH
where bun >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "%USERPROFILE%\.bun\bin\bun.exe" (
        set "PATH=%USERPROFILE%\.bun\bin;%PATH%"
        echo [INFO] Added Bun to PATH from %USERPROFILE%\.bun\bin
    )
)

:: 2. Auto-detect Python in standard paths if not yet in PATH
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    for /d %%P in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%P\python.exe" (
            set "PATH=%%P;%%P\Scripts;%PATH%"
            echo [INFO] Added Python to PATH from %%P
        )
    )
)

:: 3. Verify Python availability
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3.10+ not found in PATH!
    echo Please install Python 3.10+ from https://python.org and make sure
    echo to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo [OK] Python found: %%V

:: 4. Verify Bun availability or offer to install it
where bun >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Bun not found in PATH.
    echo Attempting automatic installation of Bun via official PowerShell installer...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm bun.sh/install.ps1 | iex"
    if exist "%USERPROFILE%\.bun\bin\bun.exe" (
        set "PATH=%USERPROFILE%\.bun\bin;%PATH%"
        echo [OK] Bun installed successfully to %USERPROFILE%\.bun\bin!
    ) else (
        echo [ERROR] Failed to auto-install Bun.
        echo Please install Bun manually by running in PowerShell:
        echo   irm bun.sh/install.ps1 ^| iex
        echo.
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%V in ('bun --version 2^>^&1') do echo [OK] Bun found: v%%V
echo.

:: 5. Install Python & Nuitka dependencies
echo [1/5] Installing Python and Nuitka packaging dependencies...
python -m pip install -q -r argon_bug/requirements.txt nuitka zstandard ordered-set
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install Python dependencies via pip.
    echo.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed.
echo.

:: 6. Compile ArgonBug via Nuitka
echo [2/5] Compiling ArgonBug into standalone C/C++ executable via Nuitka...
echo (This may take 1-3 minutes on the first build while Nuitka compiles C objects)
if not exist dist mkdir dist

python -m nuitka ^
  --onefile ^
  --enable-plugin=pyside6 ^
  --windows-console-mode=disable ^
  --assume-yes-for-downloads ^
  --company-name="OpenCode Community" ^
  --product-name="ArgonBug Desktop Mascot" ^
  --file-version=2.2.7.0 ^
  --product-version=2.2.7.0 ^
  --file-description="OpenCode Desktop Companion Widget" ^
  --copyright="MIT License" ^
  --onefile-tempdir-spec="{CACHE_DIR}/OpenCode/argon_runtime/2.2.7" ^
  --output-dir=dist ^
  --output-filename=argon_bug.exe ^
  argon_bug/main.py

if not exist "dist\argon_bug.exe" (
    echo [ERROR] Nuitka compilation failed. dist\argon_bug.exe was not created.
    echo.
    pause
    exit /b 1
)
echo [OK] ArgonBug compiled successfully: dist\argon_bug.exe
echo.

:: 7. Smoke test compiled mascot binary
echo [3/5] Smoke-testing compiled mascot binary (3-second test run)...
dist\argon_bug.exe --test-run
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Mascot smoke test failed!
    echo.
    pause
    exit /b 1
)
echo [OK] Mascot smoke test passed!
echo.

:: 8. Embed compiled mascot into OpenCode source as compressed payload
echo [4/5] Embedding compressed mascot payload into OpenCode source...
node scripts/embed_mascot.mjs dist/argon_bug.exe
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Mascot embedding script failed!
    echo.
    pause
    exit /b 1
)
echo [OK] Mascot payload successfully embedded.
echo.

:: 9. Compile OpenCode monolith executable
echo [5/5] Building monolithic opencode.exe with Bun...
bun build --compile --target=bun-windows-x64 ./packages/cli/src/index.ts --outfile=dist/opencode.exe
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Direct bun build compile failed, trying bun run pack / build fallback...
    bun run --cwd packages/cli script/build.ts --single
)

if not exist "dist\opencode.exe" (
    if exist "packages\cli\dist\opencode.exe" (
        copy /y "packages\cli\dist\opencode.exe" "dist\opencode.exe" >nul
    )
)

if not exist "dist\opencode.exe" (
    echo [ERROR] Failed to create dist\opencode.exe
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo  BUILD SUCCESSFUL!
echo ========================================================
echo  Monolithic executable: dist\opencode.exe
for %%I in (dist\opencode.exe) do echo  File size: %%~zI bytes
echo  Embedded mascot:       dist\argon_bug.exe
for %%I in (dist\argon_bug.exe) do echo  Mascot size: %%~zI bytes
echo ========================================================
echo.
echo You can now distribute dist\opencode.exe to any Windows 10/11 PC!
echo.
pause
endlocal
