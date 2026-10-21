#!/bin/bash
set -e

# ==========================
# PostgreSQL 資料庫還原腳本 (Ubuntu)
# ==========================

# 參數設定
CONTAINER_NAME="oj-postgres"
PG_USER="onlinejudge"
DATABASE_NAME="onlinejudge"
LOG="/home/chen/oj_restore.log"

# 檢查命令行參數（本地 dump 檔案路徑）
if [ $# -eq 0 ]; then
    echo "使用方式: $0 <本地dump檔案路徑>"
    echo ""
    echo "範例:"
    echo "  $0 /home/chen/oj_backup_tmp/postgres_10min_00.dump"
    exit 1
fi

DUMP_FILE_PATH="$1"

# 檢查檔案是否存在
if [ ! -f "$DUMP_FILE_PATH" ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] 錯誤: 找不到檔案 $DUMP_FILE_PATH" | tee -a "$LOG"
    exit 1
fi

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 開始還原資料庫..." | tee -a "$LOG"
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 使用備份檔: $DUMP_FILE_PATH" | tee -a "$LOG"

# ==========================
# Step 1: 複製 dump 檔到容器
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 複製備份檔到容器..." | tee -a "$LOG"

docker cp "$DUMP_FILE_PATH" "${CONTAINER_NAME}:/tmp/restore.dump"

# ==========================
# Step 2: 整個 public schema 砍掉重建，確保是空資料庫
# 不能只靠 pg_restore --clean: 它只會刪除備份檔裡有的表，備份之後才新增的表
# (例如 app_account_examipbinding) 若有外鍵指向 app_account_user，會讓
# app_account_user 刪不掉，導致使用者資料整批匯入失敗
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 清空資料庫 (重建 public schema，舊資料將被完全刪除)..." | tee -a "$LOG"

docker exec "$CONTAINER_NAME" psql -U "$PG_USER" -d "$DATABASE_NAME" -v ON_ERROR_STOP=1 -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# ==========================
# Step 3: 還原資料庫
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 還原資料庫..." | tee -a "$LOG"

# pg_restore 有錯誤時不中斷 (set -e)，繼續清理暫存檔並提示檢查訊息
if ! docker exec "$CONTAINER_NAME" pg_restore -U "$PG_USER" -d "$DATABASE_NAME" --no-owner -v /tmp/restore.dump; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] 警告: pg_restore 有錯誤，請檢查上方訊息!" | tee -a "$LOG"
fi

# ==========================
# Step 4: 清理臨時檔案
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 清理臨時檔案..." | tee -a "$LOG"

docker exec "$CONTAINER_NAME" rm /tmp/restore.dump

# ==========================
# Step 5: 補上備份之後才新增的資料表 (備份檔的 django_migrations 不含較新的 migration)
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 執行 Django migrate..." | tee -a "$LOG"

docker exec oj-web python manage.py migrate

# ==========================
# Step 6: 顯示帳號數量，確認還原結果
# ==========================
docker exec "$CONTAINER_NAME" psql -U "$PG_USER" -d "$DATABASE_NAME" -c "SELECT count(*) AS all_users, count(*) FILTER (WHERE NOT is_staff) AS students FROM app_account_user;" | tee -a "$LOG"

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 資料庫還原完成!" | tee -a "$LOG"