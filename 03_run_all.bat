@echo off
setlocal
cd /d "%~dp0"
title GitHub Activity - Full Workflow

echo ================================================
echo STEP 1: Fetch GitHub history and generate AI notes
 echo ================================================
if not exist "github_activity.py" (
  echo [ERROR] github_activity.py was not found.
  goto :failed
)
if not exist "summarize_github_class.py" (
  echo [ERROR] summarize_github_class.py was not found.
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
  echo [ERROR] repositories.json was not found.
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
echo ================================================
echo STEP 2: Summarize students and teams
 echo ================================================
python "summarize_github_class.py" --input "github_report"
if errorlevel 1 goto :failed
echo.
echo [OK] All steps completed.
if exist "github_report\_class_summary\dashboard.html" (
  start "" "github_report\_class_summary\dashboard.html"
)
goto :end
:failed
echo.
echo [ERROR] Execution stopped. Check the messages above.
:end
echo.
pause
endlocal
