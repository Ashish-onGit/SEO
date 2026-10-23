@echo off
REM ==============================================================================
REM CampusNest UP - Automated SEO Research & Drafting System
REM Daily Scheduled Task Execution Script for Windows
REM ==============================================================================

setlocal enabledelayedexpansion

REM Set working directory to project root
cd /d "%~dp0"

echo [%date% %time%] Starting Daily SEO Automation Run... >> logs\scheduler_runner.log

REM Execute pipeline via Python in scheduled mode
python main.py --scheduled >> logs\scheduler_runner.log 2>&1

set EXIT_CODE=%ERRORLEVEL%
if %EXIT_CODE% EQU 0 (
    echo [%date% %time%] Daily SEO Run Completed Successfully (Exit Code 0). >> logs\scheduler_runner.log
) else (
    echo [%date% %time%] Daily SEO Run Encountered an Error (Exit Code %EXIT_CODE%). Check logs for details. >> logs\scheduler_runner.log
)

exit /b %EXIT_CODE%
