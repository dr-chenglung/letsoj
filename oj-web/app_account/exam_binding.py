"""
上機考試 IP 綁定 (考試模式)

規則 (只對非管理員生效，且系統設定 exam_ip_binding 為 "True" 時才啟用):
  1. 一個帳號只能從一個 IP 登入: 第一次登入時綁定，之後換電腦登入會被拒絕。
  2. 一個 IP 只能登入一個帳號: 同一台電腦換瀏覽器、開無痕視窗登入別的帳號也會被拒絕。

只在登入時檢查 (user_login)。為了不讓「綁定之前就存在的登入狀態」繞過檢查，
以下三個時機會清掉學生的登入狀態，逼學生重新登入:
  - 考試模式開關從關閉變成打開 (所有學生)
  - 後台按「清除所有綁定」(所有學生)
  - 後台按單一學生的「解除」(該學生)

前提: 伺服器必須看得到學生電腦的真實 IP。Windows Docker Desktop 需搭配
exam-lan/README.md 的 Windows 本機 nginx，否則所有人都是同一個閘道 IP。
"""

import ipaddress
import logging

from django.contrib.sessions.models import Session
from django.db import IntegrityError, transaction

from app_management.models import MySysOptions

from .models import ExamBindingRejection, ExamIPBinding, LoggedInUser, User

logger = logging.getLogger(__name__)

EXAM_OPTION_NAME = "exam_ip_binding"

# Docker / 本機內部位址: 出現這些 IP 代表伺服器看不到學生的真實 IP
_INTERNAL_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.65.0/24"),
]


def get_client_ip(request):
    # 與 user_login 相同: 取 nginx 轉過來的真正 IP
    return request.META.get("HTTP_X_REAL_IP", request.META.get("REMOTE_ADDR"))


def exam_binding_enabled():
    op = MySysOptions.objects.filter(option_name=EXAM_OPTION_NAME).first()
    return op is not None and op.option_value == "True"


def is_internal_ip(ip):
    try:
        addr = ipaddress.ip_address(ip)
    except (TypeError, ValueError):
        return True
    return any(addr in net for net in _INTERNAL_NETWORKS)


def _reject(user, ip, reason):
    ExamBindingRejection.objects.create(user=user, ip=ip, reason=reason)
    logger.warning(f"考試IP綁定拒絕: {user.username}, {ip}, {reason}")
    return False, reason


def check_and_bind(user, ip, user_agent=""):
    """
    登入時檢查 user 能否從 ip 登入；尚未綁定時順便建立綁定。
    回傳 (ok, message)。管理員一律放行。
    """
    if user.is_staff:
        return True, ""

    binding = ExamIPBinding.objects.filter(user=user).first()
    if binding is not None:
        if binding.ip == ip:
            return True, ""
        return _reject(
            user, ip,
            f"此帳號已綁定在另一台電腦({binding.ip})，請舉手找監考老師。",
        )

    # 伺服器只看到內部位址時不綁定，否則第一個人綁走後全班都會被擋
    if is_internal_ip(ip):
        return _reject(
            user, ip,
            "伺服器無法取得電腦的真實IP，請老師檢查考試模式的網路設定。",
        )

    if ExamIPBinding.objects.filter(ip=ip).exists():
        return _reject(
            user, ip,
            "這台電腦已經登入過其他帳號，每台電腦只能使用一個帳號，請舉手找監考老師。",
        )

    try:
        with transaction.atomic():
            ExamIPBinding.objects.create(user=user, ip=ip, user_agent=(user_agent or "")[:500])
    except IntegrityError:
        # 同時有兩個請求搶同一個帳號或同一個 IP: 以資料庫中先成功的那筆為準重新判斷
        return check_and_bind(user, ip, user_agent)

    logger.info(f"考試IP綁定成功: {user.username}, {ip}")
    return True, ""


def clear_student_sessions(user_ids=None):
    """
    清掉學生(非管理員)的登入狀態，逼他們重新登入(重新登入時才會經過綁定檢查)。
    user_ids 為 None 表示所有學生。回傳清掉的 session 數量。
    """
    staff_ids = {str(pk) for pk in User.objects.filter(is_staff=True).values_list("id", flat=True)}
    targets = None if user_ids is None else {str(pk) for pk in user_ids}

    count = 0
    for session in Session.objects.all():
        uid = session.get_decoded().get("_auth_user_id")
        if uid is None or uid in staff_ids:
            continue
        if targets is not None and uid not in targets:
            continue
        session.delete()
        count += 1

    # 「單一登入」記錄的舊 session_key 一併刪除，否則重新登入時會被誤記為多次登入
    logged_in = LoggedInUser.objects.filter(user__is_staff=False)
    if targets is not None:
        logged_in = logged_in.filter(user_id__in=user_ids)
    logged_in.delete()

    logger.info(f"考試模式清除學生登入狀態: {count} 個 session")
    return count
