#!/bin/bash
# 批次修改模板檔案，將 CDN 連結改為本地路徑
# 此腳本在 Docker 容器啟動時執行

echo "=========================================="
echo "更新模板檔案使用本地資源..."
echo "=========================================="

# 檢查是否已修改（避免重複修改）
if [ -f "/app/templates/.patched" ]; then
    echo "✓ 模板檔案已更新，跳過修改"
    exit 0
fi

# 定義替換函數
replace_cdn_in_file() {
    local file=$1
    if [ ! -f "$file" ]; then
        return
    fi
    
    echo "處理: $file"
    
    # 備份原始檔案
    cp "$file" "$file.bak"
    
    # 檢查是否需要加入 {% load static %}
    if grep -q "{% static" "$file" && ! grep -q "{% load static %}" "$file"; then
        # 在第一個 {% block 後加入 {% load static %}
        sed -i '0,/{% block/{/{% block/a\  {% load static %}' "$file"
    fi
    
    # Bootstrap
    sed -i 's|https://cdn\.jsdelivr\.net/npm/bootstrap@5\.3\.2/dist/css/bootstrap\.min\.css|{% static '\''vendor/bootstrap/css/bootstrap.min.css'\'' %}|g' "$file"
    sed -i 's|https://cdn\.jsdelivr\.net/npm/bootstrap@5\.3\.2/dist/js/bootstrap\.bundle\.min\.js|{% static '\''vendor/bootstrap/js/bootstrap.bundle.min.js'\'' %}|g' "$file"
    
    # Font Awesome
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/6\.5\.1/css/all\.min\.css|{% static '\''vendor/fontawesome/css/all.min.css'\'' %}|g' "$file"
    
    # jQuery
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/jquery/3\.1\.0/jquery\.min\.js|{% static '\''vendor/jquery/jquery.min.js'\'' %}|g' "$file"
    
    # Highlight.js
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/highlight\.js/11\.7\.0/styles/default\.min\.css|{% static '\''vendor/highlight/default.min.css'\'' %}|g' "$file"
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/highlight\.js/11\.7\.0/highlight\.min\.js|{% static '\''vendor/highlight/highlight.min.js'\'' %}|g' "$file"
    
    # CodeMirror
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/codemirror/5\.65\.5/codemirror\.min\.css|{% static '\''vendor/codemirror/codemirror.min.css'\'' %}|g' "$file"
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/codemirror/5\.65\.5/theme/monokai\.min\.css|{% static '\''vendor/codemirror/theme/monokai.min.css'\'' %}|g' "$file"
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/codemirror/5\.65\.5/codemirror\.min\.js|{% static '\''vendor/codemirror/codemirror.min.js'\'' %}|g' "$file"
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/codemirror/5\.65\.5/mode/clike/clike\.min\.js|{% static '\''vendor/codemirror/mode/clike/clike.min.js'\'' %}|g' "$file"
    
    # MathJax
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/mathjax/3\.2\.2/es5/tex-chtml-full\.min\.js|{% static '\''vendor/mathjax/tex-chtml-full.min.js'\'' %}|g' "$file"
    
    # Chart.js
    sed -i 's|https://cdn\.jsdelivr\.net/npm/chart\.js[^"]*|{% static '\''vendor/chartjs/chart.umd.min.js'\'' %}|g' "$file"
    sed -i 's|https://cdn\.jsdelivr\.net/npm/chartjs-plugin-datalabels@2[^"]*|{% static '\''vendor/chartjs/chartjs-plugin-datalabels.min.js'\'' %}|g' "$file"
    
    # Moment.js
    sed -i 's|https://cdn\.jsdelivr\.net/npm/moment@2\.30\.1/moment\.min\.js|{% static '\''vendor/moment/moment.min.js'\'' %}|g' "$file"
    
    # Marked.js
    sed -i 's|https://cdnjs\.cloudflare\.com/ajax/libs/marked/7\.0\.0/marked\.min\.js|{% static '\''vendor/marked/marked.min.js'\'' %}|g' "$file"
}

# 尋找並處理所有 HTML 模板
find /app/app_management/templates -name "*.html" -type f | while read file; do
    replace_cdn_in_file "$file"
done

find /app/app_oj/templates -name "*.html" -type f | while read file; do
    replace_cdn_in_file "$file"
done

# 建立標記檔案
mkdir -p /app/templates
touch /app/templates/.patched

echo "✓ 模板檔案更新完成"
echo "=========================================="
