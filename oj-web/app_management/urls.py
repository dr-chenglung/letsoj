from django.urls import path
from . import views
from django.contrib.admin.views.decorators import staff_member_required

# app_name = "app_management"

urlpatterns = [
    path("", views.management, name="home_management"),
    path("problem_list/", views.problem_list, name="problem_list"),
    path("problem_create", views.problem_create, name="problem_create"),
    path("problem_update/<int:pk>/", views.problem_update, name="problem_update"),
    path(
        "problem_duplicate/<int:pk>/", views.problem_duplicate, name="problem_duplicate"
    ),
    path("problem_delete/<int:pk>/", views.problem_delete, name="problem_delete"),
    path(
        "problem_belongs_to/<int:pk>/",
        views.problem_belongs_to,
        name="problem_belongs_to",
    ),
    path(
        "problem_add_to_contests_by_ids/<int:pk>/",
        views.problem_add_to_contests_by_ids,
        name="problem_add_to_contests_by_ids",
    ),
    path("contest_list_manage/", views.contest_list_manage, name="contest_list_manage"),
    path(
        "contest_problems_manage/<int:contest_pk>/",
        views.contest_problems_manage,
        name="contest_problems_manage",
    ),
    path(
        "contest_add_problems_by_ids/<int:contest_pk>/",
        views.contest_add_problems_by_ids,
        name="contest_add_problems_by_ids",
    ),
    path("contest_create/", views.contest_create, name="contest_create"),
    path("contest_update/<int:pk>/", views.contest_update, name="contest_update"),
    path(
        "contest_duplicate/<int:pk>/", views.contest_duplicate, name="contest_duplicate"
    ),
    path("contest_delete/<int:pk>/", views.contest_delete, name="contest_delete"),
    path(
        "contest_owns_problems/<int:contest_pk>/",
        views.contest_owns_problems,
        name="contest_owns_problems",
    ),
    # Update contest visibility and start time using ajax
    path(
        "update_contest_publicity/",
        views.update_contest_publicity,
        name="update_contest_publicity",
    ),
    path(
        "update_contest_start_time/",
        views.update_contest_start_time,
        name="update_contest_start_time",
    ),
    path(
        "update_contest_end_time/",
        views.update_contest_end_time,
        name="update_contest_end_time",
    ),
    path(
        "update_solution_release_policy/",
        views.update_solution_release_policy,
        name="update_solution_release_policy",
    ),
    # Update problem belongs to
    path(
        "update_contest_owns_problems/",
        views.update_contest_owns_problems,
        name="update_contest_owns_problems",
    ),
    # 注意restful api需有staff_member_required，否則任何人皆可
    path("sys_options/", staff_member_required(views.WebsiteConfigAPI.as_view())),
    path("manage_contest/", views.manage_contest, name="manage_contest"),
    path("get_abnormal_users/", views.get_abnormal_users, name="get_abnormal_users"),
    path(
        "delete_abnormal_users/",
        views.delete_abnormal_users,
        name="delete_abnormal_users",
    ),
    path(
        "delete_user_sessions/", views.delete_user_sessions, name="delete_user_sessions"
    ),
    # 下載排名
    path(
        "ranking_download/<int:contest_pk>/",
        views.ranking_download,
        name="ranking_download",
    ),
    # 匯入使用者
    path(
        "import_users_from_excel/",
        views.import_users_from_excel,
        name="import_users_from_excel",
    ),
    # 匯出入題目
    path(
        "import_problems_from_excel/",
        views.import_problems_from_excel,
        name="import_problems_from_excel",
    ),
    path('export_problems_to_excel/', views.export_problems_to_excel, name="export_problems_to_excel"),
    # 匯出總成績表(期末成績)
    path(
        "export_all_scores_to_excel/",
        views.export_all_scores_to_excel,
        name="export_all_scores_to_excel",
    ),
    # 匯出缺考者
    path(
        "export_absent_students/",
        views.export_absent_students,
        name="export_absent_students",
    ),
    # 管理者提交答案
    path("problem_submit/<int:pk>/", views.problem_submit, name="problem_submit"),
    path("submit_to_judger/", views.submit_to_judger, name="submit_to_judger"),
    path(
        "get_manager_submission_result/",
        views.get_manager_submission_result,
        name="get_manager_submission_result",
    ),
    # 學生程式碼查閱
    path(
        "student_code_viewer/",
        views.student_code_viewer,
        name="student_code_viewer",
    ),
    # 匯出競賽提交記錄
    path(
        "export_contest_submissions/",
        views.export_contest_submissions,
        name="export_contest_submissions",
    ),
    # 匯入競賽提交記錄
    path(
        "import_contest_submissions/",
        views.import_contest_submissions,
        name="import_contest_submissions",
    ),
    # 完整競賽匯出
    path(
        "export_contest/",
        views.export_contest,
        name="export_contest",
    ),
    # 完整競賽匯入
    path(
        "import_contest/",
        views.import_contest,
        name="import_contest",
    ),
]
