from django.contrib import admin

from django.http import HttpResponse

from .models import (
    Contest,
    Problem,
    MySysOptions,
    ContestProblem,
    ProblemCategory,
    Language,
    News,
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export.tmp_storages import CacheStorage
from import_export.formats.base_formats import CSV, XLSX

# Register MySysOptions
admin.site.register(MySysOptions)


# ContestProblemInline
class ContestProblemInline(admin.TabularInline):
    model = ContestProblem
    extra = 1


class ContestResource(resources.ModelResource):
    class Meta:
        model = Contest
        # You can specify fields to exclude or include
        exclude = ("id",)  # Example: Exclude 'id'
        # export_order = [field.name for field in model._meta.fields if field.name != 'id']
        import_id_fields = []  # Do not use 'id' as import id field


class ContestAdmin(ImportExportModelAdmin):
    resource_class = ContestResource
    inlines = (ContestProblemInline,)
    list_display = (
        "id",
        "title",
        "is_visible",
        "display_seq",
        "start_time",
        "end_time",
        "created_at",
    )
    list_filter = ("is_visible",)

    search_fields = ("title",)

    # for import and export
    formats = [CSV, XLSX]
    # formats = [CSV]
    tmp_storage_class = CacheStorage

    actions = ["export_selected_contests"]

    def export_selected_contests(self, request, queryset):
        resource = self.resource_class()
        dataset = resource.export(queryset)
        file_format = self.formats[1]()  # Default to CSV
        export_data = file_format.export_data(dataset)
        response = HttpResponse(export_data, content_type=file_format.CONTENT_TYPE)
        response["Content-Disposition"] = (
            f'attachment; filename="contests.{file_format.get_extension()}"'
        )
        return response


admin.site.register(Contest, ContestAdmin)


# 可以匯出選擇的多個或全部題目
class ProblemResource(resources.ModelResource):
    class Meta:
        model = Problem
        exclude = ("id",)  # Exclude 'id'
        # export_order = [field.name for field in model._meta.fields if field.name != 'id']
        # fields = ('id', 'category', 'title', 'description', 'created_at', 'modified_at')
        # fields = ('category', 'title', 'description', 'created_at', 'modified_at')  # Exclude 'id'
        # export_order = fields
        import_id_fields = []  # Do not use 'id' as import id field


# @admin.register(Problem)
class ProblemAdmin(ImportExportModelAdmin):
    #
    resource_class = ProblemResource

    inlines = (ContestProblemInline,)

    list_display = ("id", "title", "get_categories", "language", "created_at")
    search_fields = ("title",)

    list_filter = ("language", "categories")

    # for import and export
    formats = [CSV, XLSX]
    # formats = [CSV]
    tmp_storage_class = CacheStorage

    actions = ["export_selected_problems"]

    def get_categories(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])

    get_categories.short_description = "Categories"  # Column header in admin欄位名稱

    # 可以匯出選擇的多個或全部題目
    # 匯入功能可以由amdin頁面上的按鈕執行
    def export_selected_problems(self, request, queryset):
        resource = self.resource_class()
        dataset = resource.export(queryset)
        file_format = self.formats[1]()  # Default to CSV
        export_data = file_format.export_data(dataset)
        response = HttpResponse(export_data, content_type=file_format.CONTENT_TYPE)
        response["Content-Disposition"] = (
            f'attachment; filename="problems.{file_format.get_extension()}"'
        )
        return response

    export_selected_problems.short_description = "Export selected problems"



admin.site.register(Problem, ProblemAdmin)


class ContestProblemResource(resources.ModelResource):
    class Meta:
        model = ContestProblem
        exclude = ("id",)
        import_id_fields = []  # Do not use 'id' as import id field


class ContestProblemAdmin(ImportExportModelAdmin):
    resource_class = ContestProblemResource


# Replace original registration
admin.site.register(ContestProblem, ContestProblemAdmin)


class NewsResource(resources.ModelResource):
    class Meta:
        model = News
        exclude = ("id",)
        import_id_fields = []  # Do not use 'id' as import id field


class NewsAdmin(ImportExportModelAdmin):
    resource_class = NewsResource


# Replace original registration
admin.site.register(News, NewsAdmin)


# ProblemCategory
class ProblemCategoryResource(resources.ModelResource):
    class Meta:
        model = ProblemCategory
        exclude = ("id",)
        import_id_fields = []  # Do not use 'id' as import id field


class ProblemCategoryAdmin(ImportExportModelAdmin):
    resource_class = ProblemCategoryResource


admin.site.register(ProblemCategory, ProblemCategoryAdmin)


# Language
class LanguageResource(resources.ModelResource):
    class Meta:
        model = Language
        exclude = ("id",)
        import_id_fields = []  # Do not use 'id' as import id field


class LanguageAdmin(ImportExportModelAdmin):
    resource_class = LanguageResource
    list_display = ("id", "name", "judge_id", "is_default")


admin.site.register(Language, LanguageAdmin)
