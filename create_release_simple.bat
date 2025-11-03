@echo off
echo Creating GitHub Release v1.4...
echo.
"C:\Program Files\GitHub CLI\gh.exe" release create v1.4 --title "SyncBackup v1.4 - Windows Service Fixes" --notes-file GITHUB_RELEASE_v1.4.md
echo.
echo Done!
pause
