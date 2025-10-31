#!/bin/bash
# 下載所有 CDN 資源到本地
# 此腳本在 Docker 容器啟動時執行

echo "=========================================="
echo "下載 CDN 資源到本地..."
echo "=========================================="

# 建立目錄結構
mkdir -p /app/static/vendor/bootstrap/css
mkdir -p /app/static/vendor/bootstrap/js
mkdir -p /app/static/vendor/fontawesome/css
mkdir -p /app/static/vendor/fontawesome/webfonts
mkdir -p /app/static/vendor/jquery
mkdir -p /app/static/vendor/highlight
mkdir -p /app/static/vendor/codemirror/theme
mkdir -p /app/static/vendor/codemirror/mode/clike
mkdir -p /app/static/vendor/mathjax
mkdir -p /app/static/vendor/chartjs
mkdir -p /app/static/vendor/moment
mkdir -p /app/static/vendor/marked
mkdir -p /app/static/vendor/easymde
mkdir -p /app/static/vendor/ace
mkdir -p /app/static/vendor/autosize

# 檢查是否已下載（避免重複下載）
# 因為使用 volume 掛載，資源會保存在主機，所以只需下載一次
if [ -f "/app/static/vendor/.downloaded" ]; then
    echo "✓ CDN 資源已存在，跳過下載"
    echo "✓ 資源位置: /app/static/vendor/"
    exit 0
fi

echo "開始下載資源（首次啟動，約需 1-2 分鐘）..."

# 下載 Bootstrap
echo "下載 Bootstrap..."
wget -q https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css -O /app/static/vendor/bootstrap/css/bootstrap.min.css
wget -q https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js -O /app/static/vendor/bootstrap/js/bootstrap.bundle.min.js

# 下載 Font Awesome
echo "下載 Font Awesome..."
wget -q https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css -O /app/static/vendor/fontawesome/css/all.min.css
wget -q https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.woff2 -O /app/static/vendor/fontawesome/webfonts/fa-solid-900.woff2
wget -q https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-regular-400.woff2 -O /app/static/vendor/fontawesome/webfonts/fa-regular-400.woff2
wget -q https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-brands-400.woff2 -O /app/static/vendor/fontawesome/webfonts/fa-brands-400.woff2

# 下載 jQuery
echo "下載 jQuery..."
wget -q https://cdnjs.cloudflare.com/ajax/libs/jquery/3.1.0/jquery.min.js -O /app/static/vendor/jquery/jquery.min.js

# 下載 Highlight.js
echo "下載 Highlight.js..."
wget -q https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js -O /app/static/vendor/highlight/highlight.min.js
wget -q https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/default.min.css -O /app/static/vendor/highlight/default.min.css

# 下載 CodeMirror
echo "下載 CodeMirror..."
wget -q https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.js -O /app/static/vendor/codemirror/codemirror.min.js
wget -q https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.css -O /app/static/vendor/codemirror/codemirror.min.css
wget -q https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/theme/monokai.min.css -O /app/static/vendor/codemirror/theme/monokai.min.css
wget -q https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/clike/clike.min.js -O /app/static/vendor/codemirror/mode/clike/clike.min.js

# 下載 MathJax
echo "下載 MathJax..."
wget -q https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-chtml-full.min.js -O /app/static/vendor/mathjax/tex-chtml-full.min.js

# 下載 Chart.js
echo "下載 Chart.js..."
wget -q https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js -O /app/static/vendor/chartjs/chart.umd.min.js 2>/dev/null || \
wget -q https://cdn.jsdelivr.net/npm/chart.js/dist/chart.umd.min.js -O /app/static/vendor/chartjs/chart.umd.min.js
wget -q https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js -O /app/static/vendor/chartjs/chartjs-plugin-datalabels.min.js 2>/dev/null || \
wget -q https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2/dist/chartjs-plugin-datalabels.min.js -O /app/static/vendor/chartjs/chartjs-plugin-datalabels.min.js

# 下載 Moment.js
echo "下載 Moment.js..."
wget -q https://cdn.jsdelivr.net/npm/moment@2.30.1/moment.min.js -O /app/static/vendor/moment/moment.min.js

# 下載 Marked.js
echo "下載 Marked.js..."
wget -q https://cdnjs.cloudflare.com/ajax/libs/marked/7.0.0/marked.min.js -O /app/static/vendor/marked/marked.min.js

# 下載 EasyMDE (Markdown Editor)
echo "下載 EasyMDE..."
wget -q https://cdn.jsdelivr.net/npm/easymde@1.11.2/dist/easymde.min.css -O /app/static/vendor/easymde/easymde.min.css
wget -q https://cdn.jsdelivr.net/npm/easymde@1.11.2/dist/easymde.min.js -O /app/static/vendor/easymde/easymde.min.js

# 下載 Ace Editor
echo "下載 Ace Editor..."
wget -q https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/ace.min.js -O /app/static/vendor/ace/ace.min.js

# 下載 Autosize
echo "下載 Autosize..."
wget -q https://cdn.jsdelivr.net/npm/autosize@4.0.2/dist/autosize.min.js -O /app/static/vendor/autosize/autosize.min.js

# 建立標記檔案
touch /app/static/vendor/.downloaded
echo "下載時間: $(date)" >> /app/static/vendor/.downloaded

echo "✓ 所有資源下載完成"
echo "✓ 資源已保存到主機目錄: ./oj-web/static/vendor/"
echo "✓ 下次啟動將直接使用已下載的資源"
echo "=========================================="
