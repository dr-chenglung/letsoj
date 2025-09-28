# ==========================
# 參數設定
# ==========================

# Windows 上備份存放資料夾
# 可以放到USB隨身碟等外接裝置 或是Google Drive等雲端同步資料夾
$backupDir = "C:\Users\clhuang\Documents\letsoj\PostgresBackups"

# Docker 容器名稱
$containerName = "oj-postgres"

# PostgreSQL 使用者名稱
$pgUser = "onlinejudge"

# 資料庫名稱
$databaseName = "onlinejudge"

# 建立備份資料夾（若不存在）
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir
}

# 產生檔名，附加時間戳 這樣會有很多備份檔案
# $timestamp = Get-Date -Format "mm"              # 只用分鐘數，這樣每小時只有4個備份檔案
# $timestamp = Get-Date -Format "yyyyMMdd_HHmmss" # 用完整時間戳 這樣每次備份都會有新檔案

# $dumpFileName = "pg_backup_$timestamp.dump"
# $dumpFilePath = Join-Path $backupDir $dumpFileName

# 固定檔名，覆蓋舊檔案 這樣只會保留最新的備份檔案
$dumpFileName = "pg_backup.dump"
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
