@echo off
title DPS and Co - Website Preview (Astro)
cd /d "D:\dpsca-astro"

echo ============================================================
echo   DPS ^& Co - Website Preview (Astro dev server)
echo ============================================================
echo.
echo   The site will open automatically at http://localhost:4321/
echo   KEEP THIS WINDOW OPEN. Press Ctrl+C to stop the preview.
echo ============================================================
echo.

REM Astro opens the browser itself once the server is ready (open: true in astro.config.mjs).
call npm run dev
pause
