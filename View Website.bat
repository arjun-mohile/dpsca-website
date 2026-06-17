@echo off
title DPS and Co - Website Preview
cd /d "D:\dpsca website\dist"

echo ============================================================
echo   DPS & Co - Website Preview
echo ============================================================
echo.
echo   Your browser will open at http://localhost:8080/
echo   KEEP THIS WINDOW OPEN. Close it to stop the preview.
echo ============================================================
echo.

REM Open the browser a moment after the server starts.
start "" /min cmd /c "ping 127.0.0.1 -n 3 >nul & start http://localhost:8080/"

REM Serve the built site.
py -m http.server 8080
