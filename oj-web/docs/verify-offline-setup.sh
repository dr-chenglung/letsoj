#!/bin/bash
# 驗證離線化設定是否正確
# 可在容器內或主機上執行

echo "=========================================="
echo "驗證離線化 CDN 設定"
echo "=========================================="

ERRORS=0
WARNINGS=0

# 檢查必要的資源檔案
echo -e "\n檢查必要資源檔案..."

REQUIRED_FILES=(
    "/app/static/vendor/bootstrap/css/bootstrap.min.css"
    "/app/static/vendor/bootstrap/js/bootstrap.bundle.min.js"
    "/app/static/vendor/fontawesome/css/all.min.css"
    "/app/static/vendor/fontawesome/webfonts/fa-solid-900.woff2"
    "/app/static/vendor/jquery/jquery.min.js"
    "/app/static/vendor/highlight/highlight.min.js"
    "/app/static/vendor/highlight/default.min.css"
    "/app/static/vendor/codemirror/codemirror.min.js"
    "/app/static/vendor/codemirror/codemirror.min.css"
    "/app/static/vendor/mathjax/tex-chtml-full.min.js"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(du -h "$file" | cut -f1)
        echo "  ✓ $file ($SIZE)"
    else
        echo "  ✗ 缺少: $file"
        ((ERRORS++))
    fi
done

# 檢查標記檔案
echo -e "\n檢查標記檔案..."
if [ -f "/app/static/vendor/.downloaded" ]; then
    echo "  ✓ 資源已下載標記存在"
else
    echo "  ⚠ 資源下載標記不存在"
    ((WARNINGS++))
fi

if [ -f "/app/templates/.patched" ]; then
    echo "  ✓ 模板已修改標記存在"
else
    echo "  ⚠ 模板修改標記不存在"
    ((WARNINGS++))
fi

# 檢查模板是否仍有 CDN 連結
echo -e "\n檢查模板檔案..."
if command -v grep &> /dev/null; then
    CDN_COUNT=$(grep -r "cdn\." /app/app_management/templates/ /app/app_oj/templates/ 2>/dev/null | grep -v ".bak" | wc -l)
    if [ "$CDN_COUNT" -gt 0 ]; then
        echo "  ⚠ 發現 $CDN_COUNT 處仍使用 CDN 連結"
        ((WARNINGS++))
    else
        echo "  ✓ 所有模板已使用本地資源"
    fi
else
    echo "  ⚠ 無法檢查（grep 不可用）"
fi

# 計算總資源大小
echo -e "\n資源統計..."
if [ -d "/app/static/vendor" ]; then
    TOTAL_SIZE=$(du -sh /app/static/vendor 2>/dev/null | cut -f1)
    echo "  總大小: $TOTAL_SIZE"
fi

# 總結
echo -e "\n=========================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✓ 驗證通過！離線化設定完成"
    exit 0
else
    if [ $ERRORS -gt 0 ]; then
        echo "✗ 發現 $ERRORS 個錯誤"
    fi
    if [ $WARNINGS -gt 0 ]; then
        echo "⚠ 發現 $WARNINGS 個警告"
    fi
    echo -e "\n建議："
    if [ $ERRORS -gt 0 ]; then
        echo "  1. 執行: bash /app/download-cdn-resources.sh"
    fi
    if [ $WARNINGS -gt 0 ]; then
        echo "  2. 執行: bash /app/patch-templates.sh"
    fi
    exit 1
fi
