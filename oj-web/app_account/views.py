from django.shortcuts import redirect, render

from django.contrib.sessions.models import Session
from .models import LoggedInUser
from django.http import HttpResponseRedirect
from importlib import import_module
from django.urls import reverse

from .models import User

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from app_management.models import MySysOptions
from app_account.models import IPRegectedUser, SessionWarningUser, LoginHistory, LogoutHistory

from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.hashers import make_password

from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

import ipaddress

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


@csrf_protect
@require_http_methods(["GET", "POST"])
def user_login(request):
    if request.method == "GET":
        return render(
            request, "app_account/registration/user_login.html", {"context": {}}
        )

    # POST request handling
    username = request.POST.get(
        "username", ""
    ).strip()  # 取得username，若取得不成功，則為空字串
    password = request.POST.get("password", "")
    remember_me = request.POST.get("remember_me")  # Get the checkbox value

    # Input validation
    if not username or not password:
        messages.error(request, "請輸入使用者名稱和密碼!")
        return render(
            request,
            "app_account/registration/user_login.html",
            {"context": {"error": "Missing credentials", "username": username}},
        )

    # 這樣才抓得到nginx轉過來的真正的IP:"HTTP_X_REAL_IP"
    current_ip = request.META.get("HTTP_X_REAL_IP", request.META.get("REMOTE_ADDR"))
    # current_ip = request.META.get(settings.IP_HEADER, request.META.get("REMOTE_ADDR"))

    # current_ip = request.META.get('REMOTE_ADDR') # 佈署在非容器時OK
    # current_port = request.META.get("HTTP_X_REAL_IP", request.META.get("REMOTE_PORT")) # 這裡的port沒有辨識唯一來源

    # Authenticate the user
    # 如果沒有該使用者存在時---->登入失敗
    user = authenticate(request, username=username, password=password)
    if user is None:
        logger.warning(f"登入失敗:{{username}},{current_ip}")
        messages.error(request, "名稱或密碼不正確，請重新輸入!")
        context = {"error": "Invalid credintials", "username": username}
        return render(
            request,
            "app_account/registration/user_login.html",
            {"context": context},
        )

    # Get system settings
    # 檢查系統設定是否有限制IP登入
    sys_options = {
        item.option_name: item.option_value for item in MySysOptions.objects.all()
    }
    # <QuerySet [{'id': 1, 'key': '"allow_login_ip"', 'value': 'True'}, {'id': 2, 'key': '"allow_one_login"', 'value': 'True'}, {'id': 3, 'key': '"allowed_ip_ranges"', 'value': ['163.18.22.222']}]>
    forbid_login_ip = sys_options["forbid_login_ip"] == "True"  # convert string to bool
    forbid_login_session = (
        sys_options["forbid_login_session"] == "True"
    )  # convert string to bool

    allowed_ip_ranges = sys_options["allowed_ip_ranges"]
    # logger.info(allowed_ip_ranges)
    # logger.info(type(allowed_ip_ranges))

    # 顯示登入者資訊在logger，可以省略此步驟。此登入者不一定可以進行登入，因為有可能IP被禁止
    # if user is not None:
    #     logger.info(f"檢查使用者IP是否可登入:{ user.username}, {user.full_name}, {current_ip}")

    # IP restriction check
    # 擋掉IP---------
    # (user is not None) and forbid login ip
    if forbid_login_ip and not user.is_staff:
        if not allowed_ip_ranges:
            # if '' in allowed_ip_ranges:
            messages.error(request, "目前暫停登入!")
            context = {"error": "Login suspended", "username": username}
            return render(
                request,
                "app_account/registration/user_login.html",
                {"context": context},
            )
        ip_allowed = any(
            ipaddress.ip_address(current_ip) in ipaddress.ip_network(ip)
            for ip in allowed_ip_ranges
        )
        if not ip_allowed:
            # 以下寫法也可以
            # if not any(ipaddress.IPv4Address(current_ip) in ipaddress.IPv4Network(ip) for ip in allowed_ip_ranges):
            # save rejected user
            IPRegectedUser.objects.create(user=user, ip=current_ip)
            # iprejecteduser, sucess = IPRegectedUser.objects.update_or_create(user=user, ip=current_ip)
            # msg = user.username+ ','+ str(current_ip)+"你的IP不允許參加這次的考試!"
            messages.error(request, "IP管制中,不允許此IP登入!")
            context = {"error": "IP restricted", "username": username}
            return render(
                request,
                "app_account/registration/user_login.html",
                {"context": context},
            )

    # # Login user 如果有該使用者存在，執行longin()登入動作
    # if user is not None: # 這裡不需要再次檢查
    login(request, user)  # 登入後會插入使用者資訊到request中
    logger.info(f"使用者登入成功:{ user.username}, {user.full_name}, {current_ip}")
    
    # 記錄登入歷史（包含時間、IP和瀏覽器資訊）
    try:
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # 限制長度避免過長
        LoginHistory.objects.create(
            user=user,
            ip=current_ip,
            session_key=request.session.session_key,
            user_agent=user_agent,
            is_staff_login=user.is_staff
        )
        logger.info(f"登入歷史已記錄: {user.username}, IP: {current_ip}")
    except Exception as e:
        # 記錄失敗不影響登入流程
        logger.error(f"記錄登入歷史時發生錯誤: {user.username}, {str(e)}")

    # login()之後，這時候才會是authenticated
    # if request.user.is_authenticated:
    #     logger.info("user.is_authenticated:", request.user.is_authenticated)

    # Single session management
    # 限制單一session登入  (request.user.is_authenticated)
    # if user and not user.is_staff and forbid_login_session:
    # Why request.user.is_authenticated is redundant? login() automatically authenticates the user
    if forbid_login_session and not user.is_staff:
        key_from_cookie = request.session.session_key  # 前端會啟用cookie

        # if there is a stored_session_key  in our database and it is
        # different from the current session, delete the stored_session_key
        # session_key with from the Session table
        # 使用 if hasattr(request.user, 'logged_in_user'):    else  也OK
        try:
            logged_in_user = request.user.logged_in_user  # 反向查詢
            # 另一寫法logged_in_user=LoggedInUser.objects.select_for_update().get(user=request.user)
            stored_session_key = logged_in_user.session_key
            # stored_session_key exists so delete it if it's different
            if stored_session_key != key_from_cookie:
                # print(logged_in_user,": 前一個session被刪除!")
                Session.objects.filter(session_key=stored_session_key).delete()
                # save users that login twice
                SessionWarningUser.objects.create(
                    user=request.user, ip=current_ip, session_key=stored_session_key
                )
                # logger.info(logged_in_user,": 資料庫修改保存新的session")
                #
                logged_in_user.session_key = key_from_cookie
                logged_in_user.ip = current_ip
                logged_in_user.save()
        except LoggedInUser.DoesNotExist:
            LoggedInUser.objects.create(
                user=request.user, session_key=key_from_cookie, ip=current_ip
            )

    # 到達這裡，表示使用者終於登入成功了
    # Set session expiry based on "Remember me"
    # 瀏覽器關閉後都必須要重新登入
    if remember_me:
        # Keep the session active for a long period (e.g., 30 days)
        request.session.set_expiry(1209600)  # 14 days in seconds
    else:
        # Session will expire when the user closes the browser
        request.session.set_expiry(0)

    # messages.success(request, "登入成功!") # 不會用到 因為導到首頁去了!
    if user.is_staff:
        return render(request, "app_management/home_management.html")  # 管理者首頁
        # return redirect(reverse('app_management:home_management')) # 管理者首頁

    return redirect("/")  # request資訊會一併夾帶過去
    # return redirect(reverse('app_oj:announcements'))  # 使用者首頁


@login_required
def custom_change_password(request):
    # 檢查系統設定是否允許修改密碼
    sys_options = {
        item.option_name: item.option_value for item in MySysOptions.objects.all()
    }
    # <QuerySet [{'id': 1, 'key': '"allow_login_ip"', 'value': 'True'}, {'id': 2, 'key': '"allow_one_login"', 'value': 'True'}, {'id': 3, 'key': '"allowed_ip_ranges"', 'value': ['163.18.22.222']}]>
    forbid_password_change = (
        sys_options["forbid_password_change"] == "True"
    )  # convert string to bool
    # logger.info(f"不允許修改密碼:{forbid_password_change}, {sys_options['forbid_password_change']}")
    if forbid_password_change:
        messages.error(request, "抱歉，目前不允許修改密碼!")
        return redirect("/")

    if request.method != "POST":
        return render(request, "app_account/registration/change_password.html")

    # POST request handling
    # Get password data
    old_password = request.POST.get("old_password")
    new_password1 = request.POST.get("new_password1")
    new_password2 = request.POST.get("new_password2")

    # 檢查舊密碼是否正確
    if not request.user.check_password(old_password):
        messages.error(request, "舊密碼輸入錯誤")
        return redirect("custom_change_password")

    # Validate inputs
    if not all([old_password, new_password1, new_password2]):
        messages.error(request, "所有密碼欄位都必須填寫")
        return redirect("custom_change_password")

    # Check old password
    if not request.user.check_password(old_password):
        logger.warning(f"密碼修改失敗-舊密碼錯誤: {request.user.username}")
        messages.error(request, "舊密碼輸入錯誤")
        return redirect("custom_change_password")

    # Check new passwords match
    # 檢查新密碼是否一致
    if new_password1 != new_password2:
        messages.error(request, "新密碼不一致")
        return redirect("custom_change_password")

    # Validate new password (optional)默認規則要求:最少 8 個字符 不能是純數字
    # try:
    #     validate_password(new_password1, request.user)
    # except ValidationError as e:
    #     messages.error(request, f"新密碼不符合要求: {'; '.join(e.messages)}")
    #     return redirect(reverse('custom_change_password'))

    # Update password
    # 更新密碼
    try:
        request.user.set_password(new_password1)
        request.user.save()
        # 更新 session，避免登出
        update_session_auth_hash(request, request.user)
        logger.info(f"密碼修改成功: {request.user.username}")
        messages.success(request, "密碼已成功修改")
    except Exception as e:
        logger.error(f"密碼修改發生錯誤: {request.user.username}, {str(e)}")
        messages.error(request, "密碼修改失敗，請稍後再試")

    return redirect("custom_change_password")
    # return redirect("/") # request資訊會一併夾帶過去
    # return redirect('password_change_done')


def user_register(request):
    # Check if registration is allowed
    # 檢查系統設定是否允許修改密碼
    sys_options = {
        item.option_name: item.option_value for item in MySysOptions.objects.all()
    }
    allow_user_register = sys_options.get("allow_user_register") == "True"

    if not allow_user_register:
        messages.error(request, "抱歉，目前不開放註冊!")
        return redirect("/")

    if request.method == "GET":
        return render(request, "app_account/registration/user_register.html")

    # POST handling
    # if request.method == "POST":
    user_name = request.POST["user_name"].strip()
    password = request.POST["password"]
    full_name = request.POST["full_name"].strip()
    user_class = request.POST["user_class"].strip()

    # Check if username exists
    if User.objects.filter(username=user_name).exists():
        messages.error(request, "使用者名稱已存在!")
        return redirect(reverse("user_register"))

    # Create user
    # 創建新使用者
    try:
        user = User.objects.create(
            username=user_name,
            password=make_password(password),
            full_name=full_name,
            user_class=user_class,
        )
    except:
        messages.error(request, "註冊失敗!，請再試一次")
        return redirect("user_register")

    messages.success(request, f"{user_name}註冊成功!")
    return redirect("user_register")  # 重新導向到註冊頁面
    # return redirect('user_login')  # 重新導向到註冊頁面


@login_required
def user_logout(request):
    """
    使用者登出功能
    記錄登出時間、IP和瀏覽器資訊後執行登出
    """
    # 在登出前記錄資訊（因為登出後 request.user 會變成 AnonymousUser）
    if request.user.is_authenticated:
        # 取得 IP 位址
        current_ip = request.META.get("HTTP_X_REAL_IP", request.META.get("REMOTE_ADDR"))
        
        # 記錄登出歷史
        try:
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            LogoutHistory.objects.create(
                user=request.user,
                ip=current_ip,
                session_key=request.session.session_key,
                user_agent=user_agent,
                is_staff_logout=request.user.is_staff
            )
            logger.info(f"登出歷史已記錄: {request.user.username}, IP: {current_ip}")
        except Exception as e:
            # 記錄失敗不影響登出流程
            logger.error(f"記錄登出歷史時發生錯誤: {request.user.username}, {str(e)}")
        
        # 記錄登出動作到 logger
        logger.info(f"使用者登出: {request.user.username}, {current_ip}")
    
    # 執行登出
    logout(request)
    
    # 顯示訊息並重定向
    messages.success(request, "您已成功登出！")
    return redirect("/")  # 重定向到首頁
