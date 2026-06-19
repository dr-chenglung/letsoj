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
# Step 2: 還原資料庫 (完全替換所有表)
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 還原資料庫 (舊資料將被完全刪除)..." | tee -a "$LOG"

docker exec -it "$CONTAINER_NAME" pg_restore -U "$PG_USER" -d "$DATABASE_NAME" --clean --if-exists -v /tmp/restore.dump

# ==========================
# Step 3: 清理臨時檔案
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 清理臨時檔案..." | tee -a "$LOG"

docker exec -it "$CONTAINER_NAME" rm /tmp/restore.dump

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 資料庫還原完成!" | tee -a "$LOG"