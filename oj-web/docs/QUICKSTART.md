# 快速開始：Docker 離線化設定

## 🎯 目標

將網站從使用外部 CDN 改為使用本地資源，使其能在內部網路無法連接網際網路的環境下正常運作。

## ⚡ 快速開始

### 1️⃣ 首次啟動（需要網路）

```bash
cd c:\Users\clhuang\Documents\letsoj

# 構建並啟動容器
docker-compose up --build -d

# 查看啟動日誌
docker-compose logs -f oj-web
```

容器啟動時會自動：
- ✅ 下載所有 CDN 資源（約 10-15 MB）
- ✅ 修改模板檔案使用本地路徑
- ✅ 收集靜態檔案

等待出現 "Starting Gunicorn..." 或 "Running Django development server..." 表示啟動完成。

### 2️⃣ 驗證設定

```bash
# 進入容器
docker exec -it oj-web bash

# 執行驗證腳本
bash /app/verify-offline-setup.sh

# 離開容器
exit
```

### 3️⃣ 測試網站

1. 開啟瀏覽器訪問 `http://localhost`
2. 按 F12 開啟開發者工具
3. 檢查 Network 標籤：
   - ✅ 應該看到 `/static/vendor/` 的請求
   - ❌ 不應該看到 `cdn.jsdelivr.net` 的請求

### 4️⃣ 後續啟動（可離線）

```bash
# 之後啟動不需要網路
docker-compose up -d

# 或重啟
docker-compose restart
```

## 📋 檔案說明

### 新增的檔案

| 檔案 | 說明 |
|------|------|
| `download-cdn-resources.sh` | 下載 CDN 資源腳本 |
| `patch-templates.sh` | 修改模板檔案腳本 |
| `verify-offline-setup.sh` | 驗證設定腳本 |
| `DOCKER-OFFLINE-CDN.md` | 完整說明文件 |

### 修改的檔案

| 檔案 | 修改內容 |
|------|----------|
| `entrypoint.sh` | 新增自動下載和修改邏輯 |
| `Dockerfile` | 設定腳本執行權限 |

## 🔍 常用指令

```bash
# 查看容器日誌
docker-compose logs -f oj-web

# 進入容器
docker exec -it oj-web bash

# 檢查資源檔案
docker exec -it oj-web ls -lh /app/static/vendor/

# 驗證設定
docker exec -it oj-web bash /app/verify-offline-setup.sh

# 重新收集靜態檔案
docker exec -it oj-web python manage.py collectstatic --noinput

# 重啟服務
docker-compose restart oj-web oj-nginx
```

## 🛠️ 手動操作（如需要）

### 強制重新下載資源

```bash
docker exec -it oj-web rm /app/static/vendor/.downloaded
docker exec -it oj-web bash /app/download-cdn-resources.sh
```

### 強制重新修改模板

```bash
docker exec -it oj-web rm /app/templates/.patched
docker exec -it oj-web bash /app/patch-templates.sh
```

### 還原備份

```bash
docker exec -it oj-web bash
cd /app
find . -name "*.html.bak" -exec bash -c 'mv "$0" "${0%.bak}"' {} \;
rm /app/templates/.patched
exit
```

## ❓ 疑難排解

### 問題：網頁樣式異常

```bash
# 重新收集靜態檔案
docker exec -it oj-web python manage.py collectstatic --clear --noinput

# 重啟 nginx
docker-compose restart oj-nginx
```

### 問題：資源下載失敗

```bash
# 檢查網路
docker exec -it oj-web ping -c 3 cdn.jsdelivr.net

# 手動下載
docker exec -it oj-web bash /app/download-cdn-resources.sh
```

### 問題：圖示不顯示

```bash
# 檢查字型檔案
docker exec -it oj-web ls -l /app/static/vendor/fontawesome/webfonts/

# 檢查 collectstatic
docker exec -it oj-web ls -l /app/staticfiles/vendor/fontawesome/webfonts/
```

## ✅ 檢查清單

- [ ] 容器成功啟動
- [ ] 資源檔案已下載（約 10-15 MB）
- [ ] 模板檔案已修改
- [ ] 靜態檔案已收集
- [ ] 網頁樣式正常顯示
- [ ] 圖示正常顯示
- [ ] 程式碼編輯器正常運作
- [ ] 數學公式正常渲染
- [ ] 瀏覽器 Console 無錯誤

## 📚 更多資訊

完整說明請參考：[DOCKER-OFFLINE-CDN.md](DOCKER-OFFLINE-CDN.md)

## 💡 提示

- ⏱️ 首次啟動需要 1-2 分鐘下載資源
- 🌐 首次啟動需要網路連線
- 💾 資源會持久化在 volume 中
- 🔄 後續啟動可完全離線運作
