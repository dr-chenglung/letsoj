# ==========================
# 建立 PostgreSQL 自動備份排程任務
# ==========================

# 需要以系統管理員權限執行此腳本
# powershell -ExecutionPolicy Bypass -File C:\Users\user\Documents\letsoj\scripts\setup-backup-schedule.ps1
# 或是 .\setup-backup-schedule.ps1 )

# ==========================
# 可自訂參數設定
# ==========================
$scriptPath = "C:\Users\user\Documents\letsoj\scripts\postgres-backup.ps1"
$backupIntervalMinutes = 15    # 備份間隔時間（分鐘），例如：15, 30, 60

# 可選值說明：
# $backupIntervalMinutes = 15 → 每15分鐘（00、15、30、45分執行）
# $backupIntervalMinutes = 30 → 每30分鐘（00、30分執行）
# $backupIntervalMinutes = 60 → 每1小時（整點執行）
# $backupIntervalMinutes = 10 → 每10分鐘（00、10、20、30、40、50分執行）


# 任務設定
$taskName = "PostgreSQL Auto Backup"
# 方式 1：使用當前腳本所在目錄 或是 Get-Location $PWD.Path
$workingDirectory = $PSScriptRoot

# 檢查腳本是否存在
if (!(Test-Path $scriptPath)) {
    Write-Host "錯誤: 找不到備份腳本 $scriptPath" -ForegroundColor Red
    exit 1
}

try {
    # 刪除現有的同名任務（如果存在）
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "已移除現有的排程任務" -ForegroundColor Yellow
    } catch {
        # 忽略錯誤，可能任務不存在
    }

    # 創建觸發器 - 根據設定的間隔時間執行
    $now = Get-Date
    
    # 計算下一個執行時間（對齊到間隔的整數倍）
    # 例如：間隔30分鐘，則在00分和30分執行；間隔15分鐘，則在00、15、30、45分執行
    $minutesToAdd = $backupIntervalMinutes - ($now.Minute % $backupIntervalMinutes)
    if ($minutesToAdd -eq $backupIntervalMinutes) { $minutesToAdd = 0 }
    $nextRun = $now.AddMinutes($minutesToAdd).Date.AddHours($now.AddMinutes($minutesToAdd).Hour).AddMinutes([math]::Floor($now.AddMinutes($minutesToAdd).Minute / $backupIntervalMinutes) * $backupIntervalMinutes)
    
    $trigger = New-ScheduledTaskTrigger -Once -At $nextRun -RepetitionInterval (New-TimeSpan -Minutes $backupIntervalMinutes)

    # 創建動作 - 執行 PowerShell 腳本
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`"" -WorkingDirectory $workingDirectory

    # 創建設定 - 允許任務在電腦空閒時執行，但不要求空閒
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -DontStopOnIdleEnd

    # 創建主體 - 使用當前使用者帳戶執行
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

    # 註冊排程任務
    Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Principal $principal -Description "每 $backupIntervalMinutes 分鐘自動備份 PostgreSQL 資料庫"

    Write-Host "排程任務建立成功！" -ForegroundColor Green
    Write-Host "任務名稱: $taskName"
    Write-Host "執行頻率: 每 $backupIntervalMinutes 分鐘"
    Write-Host "腳本路徑: $scriptPath"
    Write-Host "下次執行: $nextRun"
    Write-Host ""
    Write-Host "您可以在「工作排程器」中查看和管理此任務" -ForegroundColor Cyan
    Write-Host "或使用以下指令檢查任務狀態:"
    Write-Host "Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray

} catch {
    Write-Host "建立排程任務時發生錯誤: $($_.Exception.Message)" -ForegroundColor Red
}

# 顯示如何手動管理任務的指令
Write-Host ""
Write-Host "管理排程任務的 PowerShell 指令:" -ForegroundColor Cyan
Write-Host "查看任務: Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host "啟動任務: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host "停止任務: Stop-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host "刪除任務: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray