@echo off
setlocal
cd /d "%~dp0"
title GitHub Activity - Fetch and AI Summarize

echo ================================================
echo STEP 1: Fetch GitHub history and generate AI notes
 echo ================================================
if not exist "github_activity.py" (
  echo [ERROR] github_activity.py was not found in %CD%
  goto :failed
)
if not exist "run_github_activity.py" (
  echo [ERROR] run_github_activity.py was not found.
  goto :failed
)
if not exist ".env" (
  echo [ERROR] .env was not found in %CD%
  goto :failed
)
if not exist "repositories.json" (
  echo [ERROR] repositories.json was not found in %CD%
  goto :failed
)
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python is not on PATH. Activate your conda environment first.
  goto :failed
)
python "run_github_activity.py" --input "repositories.json" --ai
if errorlevel 1 goto :failed
echo.
echo [OK] GitHub activity analysis completed.
goto :end
:failed
echo.
echo [ERROR] Execution failed. Check the messages above.
:end
echo.
pause
endlocal
