# Online Judge 競賽系統 - 開發紀錄

## 📋 專案概述

這是一個基於 Django 的線上程式競賽系統（Online Judge），提供競賽管理、題目提交、自動評分等功能。系統支援多種程式語言，並具有完整的權限管理和安全機制。

## 🏗️ 系統架構

### 技術棧

- **後端**: Django 4.x
- **前端**: Bootstrap 5, HTML5, CSS3, JavaScript
- **資料庫**: PostgreSQL / SQLite
- **評分引擎**: Judge0 API
- **快取**: Redis (可選)

### 主要模組

- `app_oj`: 競賽相關功能
- `app_management`: 管理後台
- `app_account`: 用戶帳戶管理
- `website_configs`: 系統配置

## 🔒 安全機制

### 競賽訪問控制

#### 問題背景

2025年10月10日，發現競賽列表安全性問題：尚未開始的公開競賽是否會被駭客通過前端操作提前看到競賽內容。

#### 安全分析

- **後端權限檢查**: 所有競賽相關函數都有完整的狀態驗證
- **前端顯示邏輯**: 競賽列表顯示所有公開競賽
- **潛在風險**: 駭客可通過URL直接訪問或JavaScript操作繞過前端限制

#### 解決方案實施

##### 1. 前端條件渲染 (`contest_list.html`)

```html
<!-- 競賽名稱欄位 -->
{% if request.user.is_staff or contest.status != "NOT_STARTED" %}
  <a href="{% url 'contest_detail' contest.pk %}">{{ contest.title }}</a>
{% else %}
  <span class="text-muted">{{ contest.title }}</span>
{% endif %}

<!-- 排名欄位 -->
{% if request.user.is_staff or contest.status != "NOT_STARTED" %}
  <a href="{% url 'get_contest_ranking' contest.id %}"><span class="badge bg-warning rounded-pill">R</span></a>
{% else %}
  <span class="badge bg-secondary rounded-pill">R</span>
{% endif %}
```

##### 2. 權限檢查邏輯

- **管理員**: 可訪問所有競賽（包括尚未開始的）
- **普通用戶**: 只能訪問已開始的競賽
- **未登入用戶**: 只能看到已開始的競賽

##### 3. 後端保護函數

- `contest_detail()`: 競賽詳情頁面
- `get_contest_ranking()`: 競賽排名頁面
- `contest_problem_submit()`: 題目提交頁面

所有函數都包含以下權限檢查：

```python
if (
    not request.user.is_staff and contest.status is ContestStatus.CONTEST_NOT_START
) or not contest.is_public:
    return redirect("contest_list")
```

#### 安全效果

- ✅ **雙重保護**: 前端防護 + 後端權限檢查
- ✅ **用戶體驗**: 顯示所有公開競賽資訊，但控制訪問權限
- ✅ **管理功能**: 管理員保留完整訪問權限
- ✅ **防範攻擊**: 防止URL直接訪問、JavaScript操作等攻擊途徑

## 📝 開發記錄

### 2025年10月10日 - 競賽安全性改進

#### 修改內容

1. **前端模板修改** (`app_oj/templates/app_oj/contest_list.html`)
   - 添加條件渲染邏輯
   - 尚未開始競賽顯示為灰色文字
   - 排名按鈕根據狀態顯示不同樣式

2. **權限邏輯確認**
   - 驗證所有後端函數的權限檢查完整性
   - 確認雙重保護機制有效性

#### 測試項目

- ✅ 普通用戶無法訪問尚未開始競賽
- ✅ 管理員可以訪問所有競賽
- ✅ 前端顯示邏輯正確
- ✅ 後端權限檢查正常

### 之前的開發記錄

#### 題目搜尋功能改進

- **問題**: 題目列表搜尋只支援單一關鍵字
- **解決**: 實現多關鍵字AND搜尋
- **修改檔案**: `app_management/views.py`, `app_management/templates/app_management/problem_list.html`

#### 競賽管理功能

- **多關鍵字搜尋**: 競賽名稱支援空白分隔多關鍵字
- **競賽ID過濾**: 新增競賽ID搜尋功能
- **重置按鈕**: 一鍵清除所有搜尋條件

## 🚀 功能特性

### 用戶功能

- ✅ 用戶註冊/登入
- ✅ 競賽列表瀏覽
- ✅ 競賽參與與題目提交
- ✅ 即時評分結果
- ✅ 個人競賽統計
- ✅ 排名查看

### 管理功能

- ✅ 競賽管理（新增/編輯/刪除）
- ✅ 題目管理
- ✅ 用戶管理
- ✅ 系統設定
- ✅ 競賽匯出匯入

### 安全特性

- ✅ 角色-based權限控制
- ✅ 競賽狀態檢查
- ✅ 防止提前洩題
- ✅ 防範未授權訪問

## 📦 安裝說明

### 環境需求

- Python 3.8+
- Django 4.x
- PostgreSQL 或 SQLite
- Redis (推薦用於快取)

### 安裝步驟

```bash
# 1. 複製專案
git clone <repository-url>
cd oj-web

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 資料庫遷移
python manage.py makemigrations
python manage.py migrate

# 4. 建立超級用戶
python manage.py createsuperuser

# 5. 啟動開發伺服器
python manage.py runserver
```

### 設定說明

1. **資料庫設定**: 修改 `website_configs/settings.py`
2. **Judge0 API**: 設定評分引擎API位址
3. **靜態檔案**: 執行 `python manage.py collectstatic`

## 🔧 使用說明

### 管理員操作

1. 登入管理後台 (`/admin/`)
2. 建立競賽和題目
3. 設定系統參數
4. 監控競賽狀態

### 用戶操作

1. 註冊帳號
2. 瀏覽競賽列表
3. 參與競賽並提交程式碼
4. 查看評分結果和排名

## 📊 系統狀態

### 當前功能狀態

- ✅ 核心競賽功能
- ✅ 用戶管理系統
- ✅ 自動評分系統
- ✅ 安全保護機制
- ✅ 管理後台

### 已知限制

- 評分引擎依賴外部Judge0服務
- 大規模並發需要額外優化
- 部分功能尚在開發中

## 🤝 貢獻指南

### 開發規範

1. 遵循Django最佳實踐
2. 保持程式碼簡潔可讀
3. 添加適當的註釋和文檔
4. 提交前進行測試

### 安全注意事項

- 所有新功能都要進行安全審查
- 權限檢查不可或缺
- 記錄敏感操作日誌

## 📞 聯絡資訊

如有問題或建議，請聯絡開發團隊。

---

**最後更新**: 2025年10月10日
**版本**: v1.0.0
**維護者**: 開發團隊

