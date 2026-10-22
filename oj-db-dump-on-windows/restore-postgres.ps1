# ==========================
# PostgreSQL 資料庫還原腳本
# ==========================

# 參數設定
$containerName = "oj-postgres"
$pgUser = "onlinejudge"
$databaseName = "onlinejudge"
$backupDir = "..\oj-postgres-dump-backup"

$dumpFileName = "pg_backup_00.dump"
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

    # Step 2: 整個 public schema 砍掉重建，確保是空資料庫
    # 不能只靠 pg_restore --clean: 它只會刪除備份檔裡有的表，備份之後才新增的表
    # (例如 app_account_examipbinding) 若有外鍵指向 app_account_user，會讓
    # app_account_user 刪不掉，導致使用者資料整批匯入失敗
    Write-Host "清空資料庫 (重建 public schema，舊資料將被完全刪除)..." -ForegroundColor Yellow
    docker exec $containerName psql -U $pgUser -d $databaseName -v ON_ERROR_STOP=1 -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    if ($LASTEXITCODE -ne 0) { throw "清空資料庫失敗" }

    # Step 3: 還原資料庫
    Write-Host "還原資料庫..." -ForegroundColor Green
    docker exec $containerName pg_restore -U $pgUser -d $databaseName --no-owner -v /tmp/restore.dump
    if ($LASTEXITCODE -ne 0) { Write-Host "pg_restore 有錯誤，請檢查上方訊息!" -ForegroundColor Red }

    # Step 4: 清理臨時檔案
    Write-Host "清理臨時檔案..." -ForegroundColor Green
    docker exec $containerName rm /tmp/restore.dump

    # Step 5: 補上備份之後才新增的資料表 (備份檔的 django_migrations 不含較新的 migration)
    Write-Host "執行 Django migrate..." -ForegroundColor Green
    docker exec oj-web python manage.py migrate

    # Step 6: 顯示帳號數量，確認還原結果
    docker exec $containerName psql -U $pgUser -d $databaseName -c "SELECT count(*) AS all_users, count(*) FILTER (WHERE NOT is_staff) AS students FROM app_account_user;"

    Write-Host "資料庫還原完成!" -ForegroundColor Green
}
catch {
    Write-Host "還原過程中發生錯誤: $($_.Exception.Message)" -ForegroundColor Red
    # 嘗試清理臨時檔案
    docker exec $containerName rm /tmp/restore.dump 2>$null
}