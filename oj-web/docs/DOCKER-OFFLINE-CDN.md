# Docker 自動離線化 CDN 資源

## 📋 說明

此專案在 Docker 容器啟動時會自動：
1. 下載所有外部 CDN 資源到本地 `static/vendor/` 目錄
2. 自動修改所有 HTML 模板，將 CDN 連結改為本地路徑
3. 收集靜態檔案供 nginx 使用

這樣即使在內部網路無法連接網際網路的環境，網站功能也能正常運作。

## 🚀 使用方式

### 第一次啟動

```bash
# 構建並啟動容器
docker-compose up --build

# 或者分開執行
docker-compose build
docker-compose up
```

容器啟動時會自動：
- ✅ 下載 Bootstrap, Font Awesome, jQuery 等資源
- ✅ 修改模板檔案使用本地資源
- ✅ 只執行一次（使用標記檔案避免重複）

### 後續啟動

```bash
docker-compose up
```

由於資源已下載且模板已修改，不會重複執行。

### 強制重新下載/修改

如果需要重新下載資源或修改模板：

```bash
# 進入容器
docker exec -it oj-web bash

# 刪除標記檔案
rm /app/static/vendor/.downloaded
rm /app/templates/.patched

# 重啟容器
exit
docker-compose restart oj-web
```

## 📦 下載的資源

以下資源會自動下載到 `static/vendor/` 目錄：

| 資源 | 版本 | 大小 | 用途 |
|------|------|------|------|
| Bootstrap | 5.3.2 | ~350 KB | 網頁樣式框架 |
| Font Awesome | 6.5.1 | ~3 MB | 圖示字型 |
| jQuery | 3.1.0 | ~85 KB | JavaScript 函式庫 |
| Highlight.js | 11.7.0 | ~800 KB | 程式碼語法高亮 |
| CodeMirror | 5.65.5 | ~500 KB | 程式碼編輯器 |
| MathJax | 3.2.2 | ~6 MB | 數學公式渲染 |
| Chart.js | 4.4.0 | ~300 KB | 圖表渲染 |
| Moment.js | 2.30.1 | ~70 KB | 時間處理 |
| Marked.js | 7.0.0 | ~50 KB | Markdown 渲染 |

**總計約 10-15 MB**

## 🔧 相關檔案

### 新增的檔案

1. **`download-cdn-resources.sh`**
   - 下載所有 CDN 資源的腳本
   - 使用 wget 下載檔案
   - 建立 `.downloaded` 標記避免重複

2. **`patch-templates.sh`**
   - 批次修改模板檔案的腳本
   - 使用 sed 替換 CDN 連結
   - 自動加入 `{% load static %}` 標籤
   - 建立 `.patched` 標記避免重複

### 修改的檔案

1. **`entrypoint.sh`**
   - 在容器啟動時執行下載和修改腳本
   - 只在首次啟動時執行

2. **`Dockerfile`**
   - 設定腳本執行權限

## 🔍 驗證

### 檢查資源是否下載

```bash
docker exec -it oj-web ls -lh /app/static/vendor/
```

### 檢查模板是否修改

```bash
docker exec -it oj-web grep -r "{% static 'vendor" /app/app_management/templates/
```

### 檢查網站功能

1. 開啟瀏覽器訪問網站
2. 按 F12 開啟開發者工具
3. 檢查 Network 標籤：
   - ✅ 應該看到 `/static/vendor/` 開頭的請求
   - ❌ 不應該看到 `cdn.jsdelivr.net` 或 `cdnjs.cloudflare.com` 的請求
4. 檢查 Console 標籤：
   - ✅ 不應該有載入錯誤

## 📊 容器啟動流程

```
容器啟動
    ↓
檢查 .downloaded 標記
    ↓
如果不存在 → 執行 download-cdn-resources.sh
    ↓
檢查 .patched 標記
    ↓
如果不存在 → 執行 patch-templates.sh
    ↓
執行資料庫遷移 (makemigrations/migrate)
    ↓
載入初始資料
    ↓
收集靜態檔案 (collectstatic)
    ↓
建立超級使用者
    ↓
啟動 Django 伺服器
```

## 🐛 疑難排解

### 問題 1: 資源下載失敗

```bash
# 檢查網路連線
docker exec -it oj-web ping cdn.jsdelivr.net

# 手動執行下載腳本
docker exec -it oj-web bash /app/download-cdn-resources.sh
```

### 問題 2: 模板修改失敗

```bash
# 手動執行修改腳本
docker exec -it oj-web bash /app/patch-templates.sh

# 檢查備份檔案
docker exec -it oj-web ls -l /app/app_management/templates/**/*.bak
```

### 問題 3: 網頁樣式異常

```bash
# 重新收集靜態檔案
docker exec -it oj-web python manage.py collectstatic --clear --noinput

# 重啟 nginx
docker-compose restart oj-nginx
```

### 問題 4: 想要還原原始模板

```bash
# 從備份還原
docker exec -it oj-web bash
cd /app
find . -name "*.html.bak" -exec bash -c 'mv "$0" "${0%.bak}"' {} \;
rm /app/templates/.patched
exit

# 重啟容器
docker-compose restart oj-web
```

## 🌐 離線環境部署

### 方法 1: 預先下載資源（推薦）

在有網路的環境先構建 image：

```bash
# 構建 image
docker-compose build

# 儲存 image
docker save -o oj-web-offline.tar oj-web:latest

# 複製到離線環境並載入
docker load -i oj-web-offline.tar

# 啟動
docker-compose up
```

### 方法 2: 手動複製資源

在有網路的環境：

```bash
# 啟動容器並下載資源
docker-compose up -d

# 複製資源目錄
docker cp oj-web:/app/static/vendor ./vendor-backup

# 打包
tar -czf vendor.tar.gz vendor-backup
```

在離線環境：

```bash
# 解壓
tar -xzf vendor.tar.gz

# 複製到容器（容器啟動後）
docker cp vendor-backup/. oj-web:/app/static/vendor/

# 手動執行模板修改
docker exec -it oj-web bash /app/patch-templates.sh

# 收集靜態檔案
docker exec -it oj-web python manage.py collectstatic --noinput
```

## ⚠️ 注意事項

1. **首次啟動時間**：由於需要下載資源，首次啟動會比較慢（約 1-2 分鐘）
2. **網路需求**：首次啟動需要網路連線，之後可離線運作
3. **磁碟空間**：需要額外 10-15 MB 空間存放資源
4. **Volume 掛載**：由於使用 volume 掛載 `/app`，下載的資源會持久化在主機
5. **備份建議**：修改前會自動備份模板為 `.bak` 檔案

## 🔄 更新資源版本

如果要更新 CDN 資源版本：

1. 編輯 `download-cdn-resources.sh` 修改版本號
2. 刪除標記檔案：
   ```bash
   docker exec -it oj-web rm /app/static/vendor/.downloaded
   ```
3. 重啟容器：
   ```bash
   docker-compose restart oj-web
   ```

## 📚 延伸閱讀

- [Django Static Files](https://docs.djangoproject.com/en/stable/howto/static-files/)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
- [Bootstrap](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)
