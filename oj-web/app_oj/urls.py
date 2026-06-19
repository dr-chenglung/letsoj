from django.urls import path
from . import views

#app_name = "app_oj"

urlpatterns = [
    # contest listing
    path("", views.announcements, name="announcements"),
    path("oj_about/", views.oj_about, name="oj_about"),
    path("learning_map/", views.learning_map, name="learning_map"),
    path("contest_list/", views.contest_list, name="contest_list"),
    path("contest/<int:contest_pk>/", views.contest_detail, name="contest_detail"),
    # submission
    path(
        "contest_problem_submit/<int:contest_pk>/<int:problem_pk>/",
        views.contest_problem_submit,
        name="contest_problem_submit",
    ),
    path("api/submit/", views.submit_to_judger, name="submit_to_judger"),
    path(
        "api/get_submission_result/",
        views.get_submission_result,
        name="get_submission_result",
    ),
    # Ranking
    path(
        "contest/ranking/<int:contest_id>/",
        views.get_contest_ranking,
        name="get_contest_ranking",
    ),
    # user_contest_summary
    path(
        "user_contests_summary/",
        views.user_contests_summary,
        name="user_contests_summary",
    ),
]
