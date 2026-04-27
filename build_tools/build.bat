@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  build.bat — Compilation complète Clean Manager ERP
REM  Usage : double-cliquez ou lancez depuis la RACINE du projet
REM           build_tools\build.bat
REM ═══════════════════════════════════════════════════════════════════════════
setlocal EnableDelayedExpansion
cd /d "%~dp0.."

set GREEN=[92m
set RED=[91m
set YELLOW=[93m
set CYAN=[96m
set RESET=[0m

echo.
echo %CYAN% ╔══════════════════════════════════════════╗%RESET%
echo %CYAN% ║   Clean Manager ERP -- Build Script      ║%RESET%
echo %CYAN% ╚══════════════════════════════════════════╝%RESET%
echo.

for /f "tokens=*" %%v in ('python -c "from __version__ import __version__; print(__version__)" 2^>nul') do set APP_VERSION=%%v
if "!APP_VERSION!"=="" set APP_VERSION=1.1.0
echo %CYAN%[INFO]%RESET% Version : !APP_VERSION!

REM ─── ETAPE 1 : Python ──────────────────────────────────────────────────────
echo.
echo %CYAN%[1/7] Verification Python...%RESET%
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERREUR] Python introuvable. Installez Python 3.11+ depuis https://python.org%RESET%
    echo          Cochez "Add Python to PATH" pendant l'installation.
    pause & exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo %GREEN%[OK]%RESET% Python !PY_VER!

python -c "import struct; assert struct.calcsize('P')*8==64" 2>nul
if errorlevel 1 ( echo %RED%[ERREUR] Python 32-bit detecte. PyQt6 necessite Python 64-bit.%RESET% & pause & exit /b 1 )
echo %GREEN%[OK]%RESET% Architecture 64-bit

python -c "import sys; assert sys.version_info>=(3,11)" 2>nul
if errorlevel 1 ( echo %YELLOW%[AVERT] Python 3.11+ recommande.%RESET% )



REM ─── ETAPE 3 : Tests pre-build ─────────────────────────────────────────────
echo.
echo %CYAN%[3/7] Verification des fichiers requis...%RESET%
set BUILD_OK=1
for %%f in (main.py assets\logo-entreprise.ico assets\styles.qss config\entreprise.json templates\payslip\default.html) do (
    if not exist "%%f" (
        echo %YELLOW%[AVERT] Fichier manquant : %%f%RESET%
        set BUILD_OK=0
    ) else (
        echo %GREEN%[OK]%RESET% %%f
    )
)
if "!BUILD_OK!"=="0" (
    echo %YELLOW%[AVERT] Des fichiers sont manquants. La compilation peut echouer.%RESET%
    echo  Appuyez sur une touche pour continuer quand meme, ou Ctrl+C pour annuler.
    pause >nul
)

REM ─── ETAPE 4 : Nettoyage ───────────────────────────────────────────────────
echo.
echo %CYAN%[4/7] Nettoyage anciens builds...%RESET%
if exist "dist\CleanManagerERP"  rmdir /s /q "dist\CleanManagerERP"
if exist "build\CleanManagerERP" rmdir /s /q "build\CleanManagerERP"
echo %GREEN%[OK]%RESET% Nettoyage termine

REM ─── ETAPE 5 : PyInstaller ─────────────────────────────────────────────────
echo.
echo %CYAN%[5/7] Compilation PyInstaller (2-5 min)...%RESET%
echo.
python -m PyInstaller build_tools\clean_manager.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo %RED%[ERREUR] Compilation echouee.%RESET%
    echo  Causes frequentes :
    echo    - Module manquant : ajoutez-le dans hiddenimports du .spec
    echo    - Antivirus : ajoutez une exclusion pour le dossier build/
    echo    - Mauvais repertoire : lancez depuis la RACINE du projet
    pause & exit /b 1
)
if not exist "dist\CleanManagerERP\CleanManagerERP.exe" (
    echo %RED%[ERREUR] CleanManagerERP.exe introuvable apres compilation.%RESET%
    pause & exit /b 1
)
for %%I in ("dist\CleanManagerERP\CleanManagerERP.exe") do set /a EXE_MB=%%~zI/1048576
echo.
echo %GREEN%[OK]%RESET% CleanManagerERP.exe cree (~!EXE_MB! Mo)

REM ─── ETAPE 6 : Preparation distribution ────────────────────────────────────
echo.
echo %CYAN%[6/7] Preparation distribution...%RESET%
for %%d in (database logs exports reports) do (
    if not exist "dist\CleanManagerERP\%%d" mkdir "dist\CleanManagerERP\%%d"
)
if exist "tools\migrate.py"  copy /y "tools\migrate.py"  "dist\CleanManagerERP\migrate.py"  >nul
if exist "LICENSE.txt"       copy /y "LICENSE.txt"       "dist\CleanManagerERP\LICENSE.txt" >nul
if exist "README.md"         copy /y "README.md"         "dist\CleanManagerERP\LISEZ-MOI.txt" >nul

REM Calculer taille totale
set DIST_BYTES=0
for /r "dist\CleanManagerERP" %%f in (*) do set /a DIST_BYTES+=%%~zf
set /a DIST_MB=!DIST_BYTES!/1048576
echo %GREEN%[OK]%RESET% Distribution prete (~!DIST_MB! Mo au total)

REM ─── ETAPE 7 : Inno Setup (optionnel) ──────────────────────────────────────
echo.
echo %CYAN%[7/7] Recherche Inno Setup...%RESET%
set ISCC_PATH=
for %%p in (
    "C:\Program Files (x86)\Inno Setup 6\iscc.exe"
    "C:\Program Files\Inno Setup 6\iscc.exe"
    "C:\Program Files (x86)\Inno Setup 5\iscc.exe"
    "C:\Program Files\Inno Setup 5\iscc.exe"
) do ( if exist %%p if "!ISCC_PATH!"=="" set ISCC_PATH=%%p )

if not "!ISCC_PATH!"=="" (
    echo %GREEN%[OK]%RESET% Inno Setup trouve
    if not exist "dist\installer" mkdir "dist\installer"
    !ISCC_PATH! "build_tools\create_installer.iss" /Q
    if errorlevel 1 (
        echo %YELLOW%[AVERT] Inno Setup a signale une erreur.%RESET%
    ) else (
        if exist "dist\installer\CleanManagerERP_Setup_!APP_VERSION!.exe" (
            for %%I in ("dist\installer\CleanManagerERP_Setup_!APP_VERSION!.exe") do set /a SETUP_MB=%%~zI/1048576
            echo %GREEN%[OK]%RESET% Installateur cree : CleanManagerERP_Setup_!APP_VERSION!.exe ^(~!SETUP_MB! Mo^)
        )
    )
) else (
    echo %YELLOW%[INFO]%RESET% Inno Setup non installe.
    echo        Telechargez-le : https://jrsoftware.org/isinfo.php
    echo        Puis ouvrez : build_tools\create_installer.iss ^> Ctrl+F9
)

REM ─── RESUME ────────────────────────────────────────────────────────────────
echo.
echo %CYAN% ╔══════════════════════════════════════════════════════════════╗%RESET%
echo %CYAN% ║  BUILD TERMINE AVEC SUCCES                                   ║%RESET%
echo %CYAN% ╠══════════════════════════════════════════════════════════════╣%RESET%
echo %CYAN% ║%RESET%  Exe portable   : dist\CleanManagerERP\CleanManagerERP.exe    %CYAN%║%RESET%
if exist "dist\installer\CleanManagerERP_Setup_!APP_VERSION!.exe" (
    echo %CYAN% ║%RESET%  Installateur  : dist\installer\CleanManagerERP_Setup_!APP_VERSION!.exe  %CYAN%║%RESET%
) else (
    echo %CYAN% ║%RESET%  Installateur  : non genere ^(Inno Setup absent^)              %CYAN%║%RESET%
)
echo %CYAN% ╚══════════════════════════════════════════════════════════════╝%RESET%
echo.
pause
