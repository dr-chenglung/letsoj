from django.contrib import admin
from .models import LoggedInUser, IPRegectedUser, SessionWarningUser, LoginHistory, LogoutHistory
from django.contrib.auth.admin import UserAdmin
from .models import User
from import_export.admin import ImportExportModelAdmin
from import_export import resources

admin.site.register(LoggedInUser)
admin.site.register(IPRegectedUser)
admin.site.register(SessionWarningUser)


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """登入歷史記錄的管理界面"""
    list_display = ('user', 'get_full_name', 'ip', 'login_time', 'is_staff_login', 'get_short_user_agent')
    list_filter = ('login_time', 'is_staff_login', 'user')
    search_fields = ('user__username', 'user__full_name', 'ip')
    readonly_fields = ('user', 'ip', 'session_key', 'login_time', 'user_agent', 'is_staff_login')
    date_hierarchy = 'login_time'
    ordering = ('-login_time',)
    list_per_page = 50
    
    def get_full_name(self, obj):
        """顯示使用者全名"""
        return obj.user.full_name or '-'
    get_full_name.short_description = '姓名'
    
    def get_short_user_agent(self, obj):
        """顯示簡短的瀏覽器資訊"""
        if obj.user_agent:
            # 提取瀏覽器類型
            ua = obj.user_agent
            if 'Chrome' in ua and 'Edg' not in ua:
                return 'Chrome'
            elif 'Edg' in ua:
                return 'Edge'
            elif 'Firefox' in ua:
                return 'Firefox'
            elif 'Safari' in ua and 'Chrome' not in ua:
                return 'Safari'
            else:
                return ua[:30] + '...' if len(ua) > 30 else ua
        return '-'
    get_short_user_agent.short_description = '瀏覽器'
    
    def has_add_permission(self, request):
        """禁止手動新增記錄"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """禁止編輯記錄"""
        return False


@admin.register(LogoutHistory)
class LogoutHistoryAdmin(admin.ModelAdmin):
    """登出歷史記錄的管理界面"""
    list_display = ('user', 'get_full_name', 'ip', 'logout_time', 'is_staff_logout', 'get_short_user_agent')
    list_filter = ('logout_time', 'is_staff_logout', 'user')
    search_fields = ('user__username', 'user__full_name', 'ip')
    readonly_fields = ('user', 'ip', 'session_key', 'logout_time', 'user_agent', 'is_staff_logout')
    date_hierarchy = 'logout_time'
    ordering = ('-logout_time',)
    list_per_page = 50
    
    def get_full_name(self, obj):
        """顯示使用者全名"""
        return obj.user.full_name or '-'
    get_full_name.short_description = '姓名'
    
    def get_short_user_agent(self, obj):
        """顯示簡短的瀏覽器資訊"""
        if obj.user_agent:
            ua = obj.user_agent
            if 'Chrome' in ua and 'Edg' not in ua:
                return 'Chrome'
            elif 'Edg' in ua:
                return 'Edge'
            elif 'Firefox' in ua:
                return 'Firefox'
            elif 'Safari' in ua and 'Chrome' not in ua:
                return 'Safari'
            else:
                return ua[:30] + '...' if len(ua) > 30 else ua
        return '-'
    get_short_user_agent.short_description = '瀏覽器'
    
    def has_add_permission(self, request):
        """禁止手動新增記錄"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """禁止編輯記錄"""
        return False


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ("id", "username", "password", "full_name", "user_class", "user_type")
        export_order = (
            "id",
            "username",
            "full_name",
            "password",
            "user_class",
            "user_type",
        )


# class UserImportExportAdmin(ImportExportModelAdmin):
#      resource_class = UserResource

# admin.site.register(User, UserImportExportAdmin)


class CustomUserAdmin(UserAdmin, ImportExportModelAdmin):

    resource_class = UserResource

    list_display = (
        "id",
        "username",
        "full_name",
        "user_class",
        "user_type",
        "is_staff",
    )

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Additional info", {"fields": ("full_name", "user_class", "user_type")}),
    )

    add_fieldsets = (
        (None, {"fields": ("username", "password1", "password2")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Additional info", {"fields": ("full_name", "user_class", "user_type")}),
    )


admin.site.register(User, CustomUserAdmin)
