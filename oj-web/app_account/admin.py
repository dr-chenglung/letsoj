from django.contrib import admin
from .models import LoggedInUser, IPRegectedUser, SessionWarningUser
from django.contrib.auth.admin import UserAdmin
from .models import User
from import_export.admin import ImportExportModelAdmin
from import_export import resources

admin.site.register(LoggedInUser)
admin.site.register(IPRegectedUser)
admin.site.register(SessionWarningUser)


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
