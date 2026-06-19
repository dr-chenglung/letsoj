#!/bin/bash

# ==========================
# PostgreSQL 資料庫還原腳本
# ==========================

# 參數設定
CONTAINER_NAME="oj-postgres"
PG_USER="onlinejudge"
DATABASE_NAME="onlinejudge"

BACKUP_DIR="$HOME/gdrive/BACKUPdump"
DUMP_FILE_NAME="pg_backup_30.dump"
DUMP_FILE_PATH="$BACKUP_DIR/$DUMP_FILE_NAME"

# 錯誤處理函數
cleanup() {
    echo -e "\033[33m清理臨時檔案...\033[0m"
    docker exec -it $CONTAINER_NAME rm /tmp/restore.dump 2>/dev/null || true
}

trap cleanup EXIT

# 檢查檔案是否存在
if [ ! -f "$DUMP_FILE_PATH" ]; then
    echo -e "\033[31m錯誤: 找不到檔案 $DUMP_FILE_PATH\033[0m"
    exit 1
fi

echo -e "\033[32m開始還原資料庫...\033[0m"

# Step 1: 複製 dump 檔到容器
echo -e "\033[32m複製備份檔到容器...\033[0m"
docker cp "$DUMP_FILE_PATH" "$CONTAINER_NAME:/tmp/restore.dump"

# Step 2: 清空資料庫中的所有對象
echo -e "\033[33m清空現有資料庫...\033[0m"
docker exec -it $CONTAINER_NAME psql -U $PG_USER -d $DATABASE_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>/dev/null || true

# Step 3: 還原資料庫
echo -e "\033[32m還原資料庫...\033[0m"
docker exec -it $CONTAINER_NAME pg_restore -U $PG_USER -d $DATABASE_NAME -v /tmp/restore.dump

echo -e "\033[32m資料庫還原完成!\033[0m"