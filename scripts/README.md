# PostgreSQL 管理腳本

此目錄包含 PostgreSQL 資料庫管理相關的 PowerShell 腳本。

## 📁 腳本說明

### 🔄 備份相關
- **`postgres-backup.ps1`** - 執行 PostgreSQL 資料庫備份
  - 建立 Docker 容器內資料庫的 dump 檔案
  - 複製到本地 Windows 目錄
  - 自動產生時間戳檔名

### 🔧 還原相關  
- **`postgres-restore.ps1`** - 還原 PostgreSQL 資料庫
  - 列出可用的備份檔案
  - 選擇要還原的備份
  - 確認後執行還原操作

### 🧹 維護相關
- **`cleanup-old-backups.ps1`** - 清理舊備份檔案
  - 刪除超過指定天數的備份
  - 預設保留最近 7 天
  - 防止磁碟空間不足

### ⏰ 排程相關
- **`setup-backup-schedule.ps1`** - 設定自動備份排程
  - 建立 Windows 工作排程器任務
  - 每30分鐘執行一次備份
  - 在整點和30分準確執行

## 🚀 使用方式

```powershell
# 切換到 scripts 目錄
cd C:\Users\clhuang\Documents\letsoj\scripts

# 執行備份
.\postgres-backup.ps1

# 設定自動備份（需要系統管理員權限）
.\setup-backup-schedule.ps1

# 還原資料庫
.\postgres-restore.ps1

# 清理舊備份
.\cleanup-old-backups.ps1
```

## 📋 目錄結構

```
letsoj/
├── scripts/                    # PowerShell 管理腳本
│   ├── postgres-backup.ps1     # 資料庫備份
│   ├── postgres-restore.ps1    # 資料庫還原  
│   ├── cleanup-old-backups.ps1 # 清理舊備份
│   └── setup-backup-schedule.ps1 # 設定排程
├── PostgresBackups/            # 備份檔案存放位置
├── docker-compose.yml          # Docker 服務配置
└── ...
```

## 🎛️ 排程任務管理

### 檢查排程任務狀態

```powershell
# 查看任務狀態
Get-ScheduledTask -TaskName "PostgreSQL Auto Backup"

# 查看任務詳細資訊（包含下次執行時間）
Get-ScheduledTask -TaskName "PostgreSQL Auto Backup" | Get-ScheduledTaskInfo

# 查看任務動作設定
(Get-ScheduledTask -TaskName "PostgreSQL Auto Backup").Actions
```

### 手動控制排程任務

```powershell
# 手動執行一次備份任務
Start-ScheduledTask -TaskName "PostgreSQL Auto Backup"

# 停止正在執行的任務
Stop-ScheduledTask -TaskName "PostgreSQL Auto Backup"

# 刪除排程任務（需要系統管理員權限）
Unregister-ScheduledTask -TaskName "PostgreSQL Auto Backup" -Confirm:$false
```

### 重新設定排程任務

```powershell
# 以系統管理員權限執行 PowerShell，然後：
cd C:\Users\clhuang\Documents\letsoj\scripts
.\setup-backup-schedule.ps1
```

## ⚠️ 注意事項

1. **執行權限**: 排程任務的建立、修改、刪除需要系統管理員權限
2. **Docker 狀態**: 確保 Docker 容器正在運行
3. **路徑設定**: 腳本中的路徑已配置好，通常無需修改
4. **備份空間**: 定期執行清理腳本避免磁碟空間不足
5. **排程檢查**: 設定排程後可用上述指令檢查執行狀態


