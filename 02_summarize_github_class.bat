@echo off
setlocal
cd /d "%~dp0"
title GitHub Activity - Class Summary

echo ================================================
echo STEP 2: Summarize students and teams
 echo ================================================
if not exist "summarize_github_class.py" (
  echo [ERROR] summarize_github_class.py was not found in %CD%
  goto :failed
)
if not exist "github_report" (
  echo [ERROR] github_report directory was not found.
  goto :failed
)
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python is not on PATH. Activate your conda environment first.
  goto :failed
)
python "summarize_github_class.py" --input "github_report"
if errorlevel 1 goto :failed
echo.
echo [OK] Class summary completed.
if exist "github_report\_class_summary\dashboard.html" (
  echo Opening dashboard...
  start "" "github_report\_class_summary\dashboard.html"
)
goto :end
:failed
echo.
echo [ERROR] Execution failed. Check the messages above.
:end
echo.
pause
endlocal
