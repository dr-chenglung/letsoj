# ==========================
# PostgreSQL 資料庫還原腳本
# ==========================

# 參數設定
$containerName = "oj-postgres"
$pgUser = "onlinejudge"
$databaseName = "onlinejudge"
$backupDir = "..\PostgresBackups"

$dumpFileName = "pg_backup_30.dump"
$dumpFilePath = Join-Path $backupDir $dumpFileName

# 檢查檔案是否存在
if (!(Test-Path $dumpFilePath)) {
    Write-Host "錯誤: 找不到檔案 $dumpFilePath" -ForegroundColor Red
    exit 1
}

Write-Host "開始還原資料庫..." -ForegroundColor Green

try {
    # Step 1: 複製 dump 檔到容器
    Write-Host "複製備份檔到容器..." -ForegroundColor Green
    docker cp "$dumpFilePath" "${containerName}:/tmp/restore.dump"

    # Step 2: 先刪除有外鍵依賴的表
    Write-Host "清理與 users 相關的依賴表..." -ForegroundColor Yellow
    docker exec -it $containerName psql -U $pgUser -d $databaseName -c "DROP TABLE IF EXISTS app_account_loginhistory CASCADE;" 2>$null
    docker exec -it $containerName psql -U $pgUser -d $databaseName -c "DROP TABLE IF EXISTS app_account_logouthistory CASCADE;" 2>$null

    # Step 3: 還原資料庫 (完全替換所有表)
    Write-Host "還原資料庫 (舊資料將被完全刪除)..." -ForegroundColor Green
    docker exec -it $containerName pg_restore -U $pgUser -d $databaseName --clean --if-exists -v /tmp/restore.dump

    # Step 4: 清理臨時檔案
    Write-Host "清理臨時檔案..." -ForegroundColor Green
    docker exec -it $containerName rm /tmp/restore.dump

    Write-Host "資料庫還原完成!" -ForegroundColor Green
}
catch {
    Write-Host "還原過程中發生錯誤: $($_.Exception.Message)" -ForegroundColor Red
    # 嘗試清理臨時檔案
    docker exec -it $containerName rm /tmp/restore.dump 2>$null
}