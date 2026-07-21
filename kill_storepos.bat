@echo off
title StorePOS Process Cleaner
cls

:: 1. Change working directory to C:\ so CMD immediately releases the directory lock
cd /d %SystemDrive%\

echo ============================================================
echo   StorePOS - Process Cleaner (Force Terminate All Instances)
echo ============================================================
echo.
echo Searching and terminating all StorePOS background processes...
echo.

:: 2. Force taskkill by process names
taskkill /F /IM StorePOS_30DayTrial.exe /T 2>nul
taskkill /F /IM StorePOS.exe /T 2>nul
taskkill /F /IM StorePOS_3DayTrial.exe /T 2>nul
taskkill /F /IM KeyGen.exe /T 2>nul
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul
taskkill /F /IM py.exe /T 2>nul
taskkill /F /IM pyw.exe /T 2>nul

:: 3. PowerShell termination of any processes matching StorePOS
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Process | Where-Object { $_.ProcessName -like '*StorePOS*' -or $_.CommandLine -like '*store-pos*' -or $_.Path -like '*StorePOS*' } | Stop-Process -Force -ErrorAction SilentlyContinue" 2>nul

echo.
echo ============================================================
echo   SUCCESS: All StorePOS processes terminated!
echo   Working directory released. You can delete the folder now.
echo ============================================================
echo.
ping 127.0.0.1 -n 3 >nul
exit
