# ==========================
# 清理舊備份檔案
# ==========================

$backupDir = "C:\Users\clhuang\Documents\letsoj\PostgresBackups"
$keepDays = 7  # 保留最近 7 天的備份

Write-Host "清理超過 $keepDays 天的備份檔案..."

if (Test-Path $backupDir) {
    $cutoffDate = (Get-Date).AddDays(-$keepDays)
    
    Get-ChildItem -Path $backupDir -Filter "*.dump" | 
        Where-Object { $_.LastWriteTime -lt $cutoffDate } | 
        ForEach-Object {
            Write-Host "刪除舊備份: $($_.Name)" -ForegroundColor Yellow
            Remove-Item $_.FullName -Force
        }
        
    Write-Host "清理完成" -ForegroundColor Green
} else {
    Write-Host "備份目錄不存在: $backupDir" -ForegroundColor Red
}