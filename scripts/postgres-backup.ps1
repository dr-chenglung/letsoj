# ==========================
# 參數設定
# ==========================

# 如果執行腳本時遇到權限問題，需先允許執行腳本
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 手動執行一次性的備份，需要以系統管理員權限執行此腳本
# .\postgres-backup.ps1

# Windows 上備份存放資料夾
# 可以放到USB隨身碟等外接裝置 或是Google Drive等雲端同步資料夾
$backupDir = "C:\Users\clhuang\Documents\letsoj\PostgresBackups"
# $backupDir = "G:\PostgresBackups" # 這是我的USB隨身碟

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
$timestamp = Get-Date -Format "mm" # 只用分鐘數，每小時只有4個備份檔案，下一小時覆蓋
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
