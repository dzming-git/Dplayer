@echo off
:: DPlayer Complete Cleanup Launcher

PowerShell -ExecutionPolicy Bypass -NoProfile -File "%~dp0clean_all_dplayer.ps1"

pause
