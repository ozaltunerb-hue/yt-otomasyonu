@echo off
chcp 65001 >nul
title DeepMyster - YouTube token yenileme
cd /d "%~dp0"
python scripts\refresh_youtube_token.py
if errorlevel 1 (
  echo.
  echo Hata oldu. Mesaji okuyup bir tusa bas.
  pause >nul
  exit /b 1
)
echo.
echo Pencere 5 saniye icinde kapanacak.
timeout /t 5 >nul
