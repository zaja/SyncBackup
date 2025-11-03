# GitHub Release Creation Script
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

gh release create v1.4 `
  --title "SyncBackup v1.4 - Windows Service Fixes" `
  --notes-file GITHUB_RELEASE_v1.4.md
