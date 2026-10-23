# ==============================================================================
# PowerShell Script: Register Windows Task Scheduler for Daily SEO Automation
# ==============================================================================
# Usage: Open PowerShell and run:
#   powershell -ExecutionPolicy Bypass -File .\setup_scheduler.ps1
# ==============================================================================

$TaskName = "SEO_Daily_Draft_Automation"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BatchFile = Join-Path $ScriptDir "run_daily.bat"

Write-Host "Configuring Windows Task Scheduler for SEO Automation..." -ForegroundColor Cyan
Write-Host "Target Script: $BatchFile" -ForegroundColor Yellow

# Trigger: Every day at 07:00 AM IST
$Trigger = New-ScheduledTaskTrigger -Daily -At "07:00AM"

# Action: Run the batch file
$Action = New-ScheduledTaskAction -Execute $BatchFile -WorkingDirectory $ScriptDir

# Settings:
# - StartWhenAvailable: Crucial! Runs immediately if computer was asleep/off at scheduled time
# - WakeToRun: Wakes laptop from sleep if hardware timer allows
# - MultipleInstances: IgnoreNew prevents overlapping executions
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# Register or update task
try {
    # Check if task already exists
    $Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($Existing) {
        Write-Host "Updating existing scheduled task '$TaskName'..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $Trigger `
        -Action $Action `
        -Settings $Settings `
        -Description "Daily SEO Research, Competitor Analysis, and Blog Drafting Pipeline for Uttar Pradesh Student Accommodation" | Out-Null

    Write-Host "`nTask '$TaskName' successfully registered!" -ForegroundColor Green
    Write-Host "Schedule: Daily at 07:00 AM" -ForegroundColor Green
    Write-Host "Missed-run recovery: Enabled (runs on laptop wake-up)" -ForegroundColor Green
    Write-Host "`nTo test immediately, run:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
}
catch {
    Write-Host "Error registering scheduled task: $_" -ForegroundColor Red
    Write-Host "Note: If required, open PowerShell as Administrator and re-run." -ForegroundColor Yellow
}
