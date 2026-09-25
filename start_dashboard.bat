@echo off
chcp 65001 >nul
title DeepMyster - Panel (http://127.0.0.1:8771)
cd /d "%~dp0"
echo Notion kayitlari cekiliyor...
python scripts\dashboard_sync.py
rem Notion verisini 10 dakikada bir tazeleyen kucuk pencere (kapatabilirsin, panel yine calisir)
start "DeepMyster - Notion senkron" /min python scripts\dashboard_sync.py --loop
start "" http://127.0.0.1:8771/dashboard.html
echo.
echo Panel acik: http://127.0.0.1:8771/dashboard.html
echo Kapatmak icin bu pencereyi kapat.
python scripts\dashboard_server.py
