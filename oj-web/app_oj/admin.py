from django.contrib import admin
from django.http import HttpResponse
from app_oj.models import (
    Submission,
    ContestRank,
)

from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export.tmp_storages import CacheStorage
from import_export.formats.base_formats import CSV, XLSX


# 若需要從另一個平台匯入考試提交資訊，可以自訂匯入和匯出的資料格式
class SubmissionResource(resources.ModelResource):
    class Meta:
        model = Submission
        # fields = ('id', 'submitted_by', 'contest', 'problem', 'source_code', 'judge_compile_output', 'judge_status_description', 'judge_status', 'submitted_at')
        # export_order = fields
        exclude = ("id",)  # Example: Exclude 'id'
        # export_order = [field.name for field in model._meta.fields if field.name != 'id']
        import_id_fields = []  # Do not use 'id' as import id field

        # 在匯入資料時，如果資料庫中已經存在相同的紀錄且內容沒有變化，這些紀錄將會被跳過，不會進行更新。這樣可以避免不必要的更新操作，提高匯入效率。
        import_id_fields = [
            "submitted_by",
            "contest",
            "problem",
        ]  # Use these fields as import id fields
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        try:
            submission = Submission.objects.get(
                submitted_by=row["submitted_by"],
                contest=row["contest"],
                problem=row["problem"],
            )
            row["id"] = submission.id
        except Submission.DoesNotExist:
            pass


@admin.register(Submission)
class SubmissionAdmin(ImportExportModelAdmin):
    resource_class = SubmissionResource
    list_filter = ("contest",)
    list_display = ("submitted_by", "contest", "problem", "submitted_at")
    search_fields = ("submitted_by", "contest", "problem")

    formats = [CSV, XLSX]
    tmp_storage_class = CacheStorage

    actions = ["export_selected_submissions"]

    def export_selected_submissions(self, request, queryset):
        resource = self.resource_class()
        dataset = resource.export(queryset)
        file_format = self.formats[0]()  # Default to CSV
        export_data = file_format.export_data(dataset)
        response = HttpResponse(export_data, content_type=file_format.CONTENT_TYPE)
        response["Content-Disposition"] = (
            f'attachment; filename="submissions.{file_format.get_extension()}"'
        )
        return response


class ContestRankResource(resources.ModelResource):
    class Meta:
        model = ContestRank
        # fields = ('id', 'submitted_by', 'contest', 'submission_count', 'accepted_count', 'total_time', 'submission_info')
        # export_order = fields
        exclude = ("id",)  # Example: Exclude 'id'
        # export_order = [field.name for field in model._meta.fields if field.name != 'id']
        import_id_fields = []  # Do not use 'id' as import id field

        # 在匯入資料時，如果資料庫中已經存在相同的紀錄且內容沒有變化，這些紀錄將會被跳過，不會進行更新。這樣可以避免不必要的更新操作，提高匯入效率。
        import_id_fields = [
            "submitted_by",
            "contest",
        ]  # Use these fields as import id fields
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        try:
            submission = Submission.objects.get(
                submitted_by=row["submitted_by"],
                contest=row["contest"],
            )
            row["id"] = submission.id
        except Submission.DoesNotExist:
            pass


@admin.register(ContestRank)
class ContestRankAdmin(ImportExportModelAdmin):
    resource_class = ContestRankResource

    list_filter = ("contest", "submitted_by")
    list_display = (
        "submitted_by",
        "contest",
    )

    # 報錯ForeignKey fields cannot be used in list_display ??
    # search_fields = ('submitted_by', 'contest')

    formats = [CSV, XLSX]
    tmp_storage_class = CacheStorage

    actions = ["export_selected_contest_ranks"]

    def export_selected_contest_ranks(self, request, queryset):
        resource = self.resource_class()
        dataset = resource.export(queryset)
        file_format = self.formats[0]()  # Default to CSV
        export_data = file_format.export_data(dataset)
        response = HttpResponse(export_data, content_type=file_format.CONTENT_TYPE)
        response["Content-Disposition"] = (
            f'attachment; filename="contest_ranks.{file_format.get_extension()}"'
        )
        return response

    # 在admin頁面上顯示的自訂名稱
    export_selected_contest_ranks.short_description = "Export selected contest ranks"


# @admin.register(Submission)
# class SubmissionAdmin(ImportExportModelAdmin):
#     resource_class = SubmissionResource
#     list_filter = ('contest',)

# @admin.register(ContestRank)
# class ContestRankAdmin(ImportExportModelAdmin):
#     resource_class = ContestRankResource
#     list_filter = ('contest',)

# 前有有@符号修飾語句，所以這裡不需要再次調用admin.site.register
# admin.site.register(ContestRank, ContestRankAdmin)


