@echo off
title DPS and Co - Weekly Blog Draft
cd /d "D:\dpsca-astro"
echo Generating this week's blog DRAFT (for partner review)...
py blog_pipeline.py generate
echo.
echo Review the file in the 'drafts' folder, then approve with:
echo    py blog_pipeline.py approve ^<slug^>
echo    npm run build
echo.
pause
