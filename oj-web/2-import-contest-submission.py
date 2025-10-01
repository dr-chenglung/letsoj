'''
使用範例
這個程式用來匯出競賽的提交資料和排名資料

進入容器
docker exec -it oj-web bash

在終端機中執行以下指令 來匯入與匯出競賽資料 例如:contest_id=255
python 1-export-contest-submission.py 255
python 2-import-contest-submission.py 255

注意: 
資料庫必須事先有建立好相同的contest,problems,user否則會失敗
若submission的id已存在，則會更新該筆資料
'''

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website_configs.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

import sys
import json

from app_oj.models import Submission, ContestRank
from app_account.models import User
from app_management.models import Contest, Problem

# 依序將 Submission、ContestRank 匯入資料庫（遇到已存在則略過或更新）。
def import_contest_data(contest_id):
    try:
        contest = Contest.objects.get(id=contest_id)
    except Contest.DoesNotExist:
        print(f"Contest with id={contest_id} does not exist.")
        return

    submissions_json = f"contest_export_submissions_{contest_id}.json"
    ranks_json = f"contest_export_ranks_{contest_id}.json"

    # 匯入 Submission
    with open(submissions_json, "r", encoding="utf-8") as f:
        submissions_data = json.load(f)
    imported_submissions = 0
    for s in submissions_data:
        try:
            user = User.objects.get(username=s["submitted_by"])
            problem = Problem.objects.get(id=s["problem_id"])
            obj, created = Submission.objects.update_or_create(
                submitted_by=user,
                contest=contest,
                problem=problem,
                defaults={
                    "source_code": s["source_code"],
                    "judge_compile_output": s["judge_compile_output"],
                    "judge_status_description": s["judge_status_description"],
                    "judge_status": s["judge_status"],
                    "submitted_at": s["submitted_at"],
                }
            )
            imported_submissions += 1
        except Exception as e:
            print(f"Failed to import submission id={s.get('id')}: {e}")

    # 匯入 ContestRank
    with open(ranks_json, "r", encoding="utf-8") as f:
        ranks_data = json.load(f)
    imported_ranks = 0
    for r in ranks_data:
        try:
            user = User.objects.get(username=r["submitted_by"])
            obj, created = ContestRank.objects.update_or_create(
                submitted_by=user,
                contest=contest,
                defaults={
                    "submission_count": r["submission_count"],
                    "accepted_count": r["accepted_count"],
                    "total_time": r["total_time"],
                    "submission_info": r["submission_info"],
                }
            )
            imported_ranks += 1
        except Exception as e:
            print(f"Failed to import rank id={r.get('id')}: {e}")

    print(f"Imported {imported_submissions} submissions and {imported_ranks} ranks for contest {contest_id}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python 10-10-import-contest-submission.py <contest_id>")
        sys.exit(1)
    contest_id = sys.argv[1]
    import_contest_data(contest_id)
