from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class UserType(models.TextChoices):
    REGULAR_USER = "REGULAR", "Regular User"
    ADMIN_USER = "ADMIN", "Admin"


# 直接繼承使用內定的AbstractUser類別比較簡單
class User(AbstractUser):
    # User name
    # username = models.TextField(unique=True)
    # full name
    full_name = models.TextField(null=True)
    # 目前沒用到這個欄位，只有使用內定的is_staff欄位
    user_type = models.TextField(default=UserType.REGULAR_USER)

    # 若有群組或班級的需求(A, B, C, D等，預設為A)，可以使用這個欄位
    user_class = models.TextField(default="A", help_text="User's assigned class group")

    # class Meta:
    #     db_table = "app_account_user"

    def __str__(self):
        return self.username


class LoggedInUser(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User, 
        related_name="logged_in_user", # 這裡定義了反向關聯的名稱，
        on_delete=models.CASCADE
    )
    # related_name='logged_in_user' 定義了反向查詢的屬性名
    # 這使得可以通過 user.logged_in_user 直接訪問相關的 LoggedInUser 實例
    # 不需要執行額外的查詢如 LoggedInUser.objects.get(user=user)
    
    # Session keys are 32 characters long
    session_key = models.CharField(max_length=32, null=True, blank=True)
    ip = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        created_at = timezone.localtime(self.created_at).strftime("%Y-%m-%d %H:%M:%S")
        return f"{self.user.username},{created_at}"


class IPRegectedUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip = models.CharField(max_length=20, null=True, blank=True)
    session_key = models.CharField(max_length=32, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        created_at = timezone.localtime(self.created_at).strftime("%Y-%m-%d %H:%M:%S")
        return f"{self.user.username},{self.ip},{created_at}"


class SessionWarningUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip = models.CharField(max_length=20, null=True, blank=True)
    session_key = models.CharField(max_length=32, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        created_at = timezone.localtime(self.created_at).strftime("%Y-%m-%d %H:%M:%S")
        return f"{self.user.username},{self.ip},{created_at},{self.session_key}"


class LoginHistory(models.Model):
    """
    記錄使用者的每次登入歷史
    包含登入時間、IP位址、session key和瀏覽器資訊
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_histories")
    ip = models.CharField(max_length=50, help_text="登入IP位址")
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="Session Key")
    login_time = models.DateTimeField(auto_now_add=True, help_text="登入時間")
    user_agent = models.TextField(null=True, blank=True, help_text="瀏覽器資訊")
    is_staff_login = models.BooleanField(default=False, help_text="是否為管理員登入")
    
    class Meta:
        ordering = ['-login_time']  # 按登入時間倒序排列
        verbose_name = "登入歷史記錄"
        verbose_name_plural = "登入歷史記錄"
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['-login_time']),
            models.Index(fields=['ip', '-login_time']),
        ]
    
    def __str__(self):
        login_time = timezone.localtime(self.login_time).strftime("%Y-%m-%d %H:%M:%S")
        return f"{self.user.username} - {self.ip} - {login_time}"


class LogoutHistory(models.Model):
    """
    記錄使用者的每次登出歷史
    包含登出時間、IP位址、session key和瀏覽器資訊
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="logout_histories")
    ip = models.CharField(max_length=50, help_text="登出IP位址")
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="Session Key")
    logout_time = models.DateTimeField(auto_now_add=True, help_text="登出時間")
    user_agent = models.TextField(null=True, blank=True, help_text="瀏覽器資訊")
    is_staff_logout = models.BooleanField(default=False, help_text="是否為管理員登出")
    
    class Meta:
        ordering = ['-logout_time']  # 按登出時間倒序排列
        verbose_name = "登出歷史記錄"
        verbose_name_plural = "登出歷史記錄"
        indexes = [
            models.Index(fields=['user', '-logout_time']),
            models.Index(fields=['-logout_time']),
            models.Index(fields=['ip', '-logout_time']),
        ]
    
    def __str__(self):
        logout_time = timezone.localtime(self.logout_time).strftime("%Y-%m-%d %H:%M:%S")
        return f"{self.user.username} - {self.ip} - {logout_time}"


"""
from django.contrib.sessions.models import Session
class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
"""
