#!/bin/bash

set -e
# ===== 設定 =====
# 每天21:30備份 (保留最近7天)
CONTAINER_NAME="oj-postgres"
PG_USER="onlinejudge"
DATABASE_NAME="onlinejudge"
TMP_DIR="/home/chen/oj_backup_tmp"
REMOTE="gdrive:ubuntu_ojdb_dump"
LOG="/home/chen/oj_backup.log"

# 檔名：根據日期生成（YYYY-MM-DD）
DATE=$(date +%Y-%m-%d)
DUMP_FILE="postgres_daily_${DATE}.dump"
DUMP_FILE_PATH="$TMP_DIR/$DUMP_FILE"

mkdir -p "$TMP_DIR"

# ==========================
# Step 1: 在容器內執行 pg_dump
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 正在備份 PostgreSQL 容器: $CONTAINER_NAME" >> "$LOG"

docker exec -t "$CONTAINER_NAME" pg_dump -U "$PG_USER" -F c -f "/tmp/$DUMP_FILE" "$DATABASE_NAME"

# ==========================
# Step 2: 複製備份檔到本地
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 複製備份檔到本地..." >> "$LOG"

docker cp "${CONTAINER_NAME}:/tmp/$DUMP_FILE" "$DUMP_FILE_PATH"

# ==========================
# Step 3: 刪除容器內的臨時備份
# ==========================
docker exec -t "$CONTAINER_NAME" rm "/tmp/$DUMP_FILE"

# ==========================
# Step 4: 上傳到 Google Drive
# ==========================
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 上傳備份到 Google Drive..." >> "$LOG"

rclone copy "$DUMP_FILE_PATH" "$REMOTE" \
  --update \
  --log-file="$LOG" \
  --log-level INFO

# ==========================
# Step 5: 清除本地暫存
# ==========================
rm -f "$DUMP_FILE_PATH"

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 備份完成" >> "$LOG"


# 列出所有備份檔案，找出時間戳早於7天前的檔案並刪除
rclone ls "$REMOTE" --log-file="$LOG" --log-level INFO | \
  while read -r size file; do
    if [[ "$file" =~ postgres_daily_([0-9]{4}-[0-9]{2}-[0-9]{2}) ]]; then
      FILE_DATE="${BASH_REMATCH[1]}"
      if [[ "$FILE_DATE" < "$CUTOFF_DATE" ]]; then
        rclone delete "$REMOTE/$file" --log-file="$LOG" --log-level INFO
      fi
    fi
  done

