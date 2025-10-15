
# 在Django中，Session主要是在後端處理的，前端無法直接操作Session

## 後端操作Session

### 設定Session值
````python
# views.py
def my_view(request):
    # 設定單一值
    request.session['username'] = 'john'
    request.session['user_id'] = 123
    
    # 設定列表或字典
    request.session['selected_items'] = ['item1', 'item2', 'item3']
    request.session['user_preferences'] = {
        'theme': 'dark',
        'language': 'zh-tw'
    }
    
    # 設定過期時間（秒）
    request.session.set_expiry(3600)  # 1小時後過期
    
    return render(request, 'template.html')
````

### 取得Session值
````python
def my_view(request):
    # 取得值（如果不存在返回None）
    username = request.session.get('username')
    
    # 取得值並設定預設值
    user_id = request.session.get('user_id', 0)
    selected_items = request.session.get('selected_items', [])
    
    # 檢查session中是否存在某個key
    if 'username' in request.session:
        username = request.session['username']
    
    # 取得所有session數據
    all_session_data = dict(request.session)
    
    return render(request, 'template.html', {
        'username': username,
        'selected_items': selected_items
    })
````

### 刪除Session值
````python
def my_view(request):
    # 刪除特定key
    if 'username' in request.session:
        del request.session['username']
    
    # 或使用pop方法
    username = request.session.pop('username', None)
    
    # 清除所有session數據
    request.session.flush()
    
    # 清除session數據但保持session key
    request.session.clear()
    
    return redirect('home')
````

## 前端操作Session

### 在Template中顯示Session值
````django-html
<!-- template.html -->
<h1>歡迎, {{ request.session.username }}</h1>

<!-- 檢查session是否存在 -->
{% if request.session.user_id %}
    <p>用戶ID: {{ request.session.user_id }}</p>
{% endif %}

<!-- 迭代session中的列表 -->
{% for item in request.session.selected_items %}
    <li>{{ item }}</li>
{% endfor %}

<!-- 顯示session中的字典值 -->
<p>主題: {{ request.session.user_preferences.theme }}</p>
````

### 前端無法直接設定Session
前端**無法直接設定**session值，只能透過以下方式：

#### 1. 透過表單提交
````django-html
<!-- 前端表單 -->
<form method="post" action="{% url 'update_preferences' %}">
    {% csrf_token %}
    <select name="theme">
        <option value="light">淺色主題</option>
        <option value="dark">深色主題</option>
    </select>
    <button type="submit">儲存偏好</button>
</form>
````

````python
# views.py
def update_preferences(request):
    if request.method == 'POST':
        theme = request.POST.get('theme')
        # 在後端設定session
        request.session['theme'] = theme
    return redirect('home')
````

#### 2. 透過AJAX請求
````javascript
// 前端JavaScript
function updateSession(key, value) {
    fetch('/update-session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'key': key,
            'value': value
        })
    });
}

// 使用
updateSession('theme', 'dark');
````

````python
# views.py
import json
from django.http import JsonResponse

def update_session_ajax(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        key = data.get('key')
        value = data.get('value')
        
        # 設定session
        request.session[key] = value
        
        return JsonResponse({'status': 'success'})
````

## Session配置

### 在settings.py中配置Session
````python
# settings.py

# Session引擎（預設使用資料庫）
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Session cookie設定
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 1209600  # 2週（秒）
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_SECURE = False  # HTTPS時設為True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Session儲存每次請求時都儲存
SESSION_SAVE_EVERY_REQUEST = False

# Session過期時間
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
````

## 實際應用範例

````python
# views.py - 購物車功能
def add_to_cart(request, product_id):
    # 取得現有購物車
    cart = request.session.get('cart', {})
    
    # 添加商品
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    
    # 儲存回session
    request.session['cart'] = cart
    
    return JsonResponse({'cart_count': sum(cart.values())})

def view_cart(request):
    cart = request.session.get('cart', {})
    # 處理購物車邏輯...
    return render(request, 'cart.html', {'cart': cart})
````

**重點總結：**
- **後端**：可以完全控制session的讀取、設定、刪除
- **前端**：只能顯示session值，無法直接修改
- **互動**：前端需透過表單提交或AJAX請求來讓後端修改session