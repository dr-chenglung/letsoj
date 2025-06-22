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


"""
from django.contrib.sessions.models import Session
class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
"""
