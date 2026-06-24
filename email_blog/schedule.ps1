# Registers Windows scheduled tasks so the blog email automation runs hands-off:
#   "DPS Blog Email - Send"     weekly  -> run.ps1 --once          (sends the approval email)
#   "DPS Blog Email - Replies"  /30 min -> run.ps1 --check-replies (reads replies & publishes)
#
# PREREQUISITES (one-time):
#   1) py blogchecker.py --encrypt        # store the Gmail App Password (encrypted)
#   2) setx BLOG_FERNET_KEY "the-key"      # persist the key (run.ps1 loads it)
#   3) Keep this repo checked out on the `main` branch so published posts deploy.
#
# Run once:   .\schedule.ps1
# Remove:     Unregister-ScheduledTask -TaskName "DPS Blog Email - Send","DPS Blog Email - Replies" -Confirm:$false

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runPs1    = Join-Path $scriptDir "run.ps1"
if (-not (Test-Path $runPs1)) { Write-Error "run.ps1 not found next to schedule.ps1"; exit 1 }

# Keep tasks resilient on laptops.
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew

function New-RunAction([string]$arg) {
    New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runPs1`" $arg" `
        -WorkingDirectory $scriptDir
}

# 1) Weekly send — Mondays at 09:00.
$sendTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am
Register-ScheduledTask -TaskName "DPS Blog Email - Send" -Force `
    -Action (New-RunAction "--once") -Trigger $sendTrigger -Settings $settings `
    -Description "Sends the weekly DPS blog approval email."

# 2) Reply check — every 30 minutes, indefinitely.
$replyTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName "DPS Blog Email - Replies" -Force `
    -Action (New-RunAction "--check-replies") -Trigger $replyTrigger -Settings $settings `
    -Description "Reads blog approval replies and publishes approved/corrected posts."

Write-Host "Registered: 'DPS Blog Email - Send' (weekly) and 'DPS Blog Email - Replies' (every 30 min)." -ForegroundColor Green
Write-Host "A reply with a .txt/.json edit is now picked up within 30 minutes and published automatically."
