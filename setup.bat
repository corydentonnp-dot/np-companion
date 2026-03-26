@echo off
cd /d "%~dp0"
echo.
echo  CareCompanion -- Fresh Machine Setup
echo  Running setup.ps1...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
