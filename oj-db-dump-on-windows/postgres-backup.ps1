# ==========================
# 參數設定
# ==========================

# 如果執行腳本時遇到權限問題，需先允許執行腳本
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 手動執行一次性的備份，需要以系統管理員權限執行此腳本
# .\postgres-backup.ps1

# Windows 上備份存放資料夾
# 可以放到USB隨身碟等外接裝置 或是Google Drive等雲端同步資料夾
$backupDir = "G:\我的雲端硬碟\BACKUPdump"

# Docker 容器名稱
$containerName = "oj-postgres"

# PostgreSQL 使用者名稱
$pgUser = "onlinejudge"

# 資料庫名稱
$databaseName = "onlinejudge"

# 備份間隔時間（分鐘）
$backupIntervalMinutes = 15

# 建立備份資料夾（若不存在）
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir
}

# 產生檔名，附加時間戳 這樣會有很多備份檔案
# 按 15 分鐘間隔取整（00, 15, 30, 45）
$minute = (Get-Date).Minute
$timestamp = "{0:D2}" -f ([int]($minute / 15) * 15)
$dumpFileName = "pg_backup_$timestamp.dump"
$dumpFilePath = Join-Path $backupDir $dumpFileName

# ==========================
# Step 1: 在容器內 pg_dump
# ==========================
Write-Host "正在備份 PostgreSQL 容器: $containerName"
docker exec -t $containerName pg_dump -U $pgUser -F c -f /tmp/$dumpFileName $databaseName

# ==========================
# Step 2: 複製備份檔到 Windows
# ==========================
Write-Host "複製備份檔到 Windows..."
docker cp "${containerName}:/tmp/$dumpFileName" $dumpFilePath

# ==========================
# Step 3: 刪除容器內的臨時備份
# ==========================
docker exec -t $containerName rm "/tmp/$dumpFileName"

Write-Host "備份完成: $dumpFilePath"

# ==========================
# Step 4: 如果是整點，創建每小時備份
# ==========================
if ((Get-Date).Minute -eq 0) {
    $hourlyTimestamp = Get-Date -Format "HH"
    $hourlyDumpFileName = "pg_backup_hourly_$hourlyTimestamp.dump"
    $hourlyDumpFilePath = Join-Path $backupDir $hourlyDumpFileName
    Copy-Item $dumpFilePath $hourlyDumpFilePath
    Write-Host "每小時備份完成: $hourlyDumpFilePath"
}

# ==========================
# Step 5: 每日備份（檔名含日期，保留最近 N 天）
# ==========================
$dailyKeepDays = 14    # 每日備份保留天數，例如 7、14、30

# 只有在這次備份檔確實存在且不是空檔時才處理，避免把失敗的備份當成每日備份
if ((Test-Path $dumpFilePath) -and ((Get-Item $dumpFilePath).Length -gt 0)) {
    $today = Get-Date -Format "yyyy-MM-dd"
    $dailyDumpFilePath = Join-Path $backupDir "pg_backup_daily_$today.dump"

    # 今天的每日備份還不存在才複製（每天只做一次）
    if (-not (Test-Path $dailyDumpFilePath)) {
        Copy-Item $dumpFilePath $dailyDumpFilePath
        Write-Host "每日備份完成: $dailyDumpFilePath"

        # 刪除超過保留天數的每日備份（依檔名中的日期判斷）
        $cutoff = (Get-Date).Date.AddDays(-$dailyKeepDays)
        Get-ChildItem $backupDir -Filter "pg_backup_daily_*.dump" | ForEach-Object {
            if ($_.BaseName -match '^pg_backup_daily_(\d{4}-\d{2}-\d{2})$') {
                $fileDate = [datetime]::ParseExact($Matches[1], 'yyyy-MM-dd', $null)
                if ($fileDate -lt $cutoff) {
                    Remove-Item $_.FullName
                    Write-Host "已刪除過期的每日備份: $($_.Name)"
                }
            }
        }
    }
}
