@echo off
REM Windows cmd version of run_demo.sh - no WSL/bash needed.
REM Usage: demo\run_demo.bat [scenario_name]

setlocal enabledelayedexpansion

set "SCENARIO=%~1"
if "%SCENARIO%"=="" set "SCENARIO=cache_invalidation"

set "SCRIPT_DIR=%~dp0"
set "SCENARIO_DIR=%SCRIPT_DIR%scenarios\%SCENARIO%"

if not exist "%SCENARIO_DIR%" (
  echo Scenario not found: %SCENARIO_DIR%
  exit /b 1
)

REM Make a temp workdir
set "WORKDIR=%TEMP%\codelens-demo-%RANDOM%-%RANDOM%"
mkdir "%WORKDIR%" >nul 2>&1

pushd "%WORKDIR%"

git init -q >nul 2>&1
git symbolic-ref HEAD refs/heads/main >nul 2>&1
git config user.email "demo@codelens.dev" >nul 2>&1
git config user.name "CodeLens Demo" >nul 2>&1

xcopy /E /Q /Y "%SCENARIO_DIR%\before\*" . >nul 2>&1
git add -A >nul 2>&1
git commit -q -m "baseline" >nul 2>&1

git checkout -q -b feature >nul 2>&1

xcopy /E /Q /Y "%SCENARIO_DIR%\after\*" . >nul 2>&1
git add -A >nul 2>&1
git commit -q -m "feature change" >nul 2>&1

if "%CODELENS_PROVIDER%"=="" set "CODELENS_PROVIDER=mock"

if "%CODELENS_PROVIDER%"=="mock" set "CODELENS_MOCK_SCRIPT=%SCENARIO_DIR%\mock_responses.json"
if "%CODELENS_PROVIDER%"=="mock" copy "%SCENARIO_DIR%\.codelens.toml" .codelens.toml >nul 2>&1

echo.
echo ==^> Running CodeLens on scenario: %SCENARIO% (provider=%CODELENS_PROVIDER%)
echo.

python -m codelens.cli --base main --head feature --pr-body "%SCENARIO_DIR%\PR_BODY.md" --repo "%WORKDIR%"

popd
rd /s /q "%WORKDIR%" 2>nul
endlocal
