
'''
使用範例
這個程式用來匯出競賽的提交資料和排名資料

進入容器
docker exec -it oj-web bash

在終端機中執行以下指令 來匯入與匯出競賽資料 例如:contest_id=255
python 1-export-contest-submission.py 255
python 2-import-contest-submission.py 255

注意: 資料庫必須事先有建立好相同的contest and problems否則會失敗
'''



# 環境變數放在settings 因此在環境變數中要加入這一行 'DJANGO_SETTINGS_MODULE': 'recommender.settings',
# 注意 settings 是放在哪一個目錄下？ 通常與 專案目錄名稱 是一樣的  我的目錄是recommender 你的呢?
# 如果 models.py有修改，資料庫遷徙之後，必須先 Shutdown Kernel並重新啟動Kernel, 再重新執行以下指令
# 

import os 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website_configs.settings")

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# 重要!
import django
django.setup()

import sys
import json

from app_oj.models import Submission, ContestRank
from app_management.models import Contest

def export_contest_data(contest_id):
    try:
        contest = Contest.objects.get(id=contest_id)
    except Contest.DoesNotExist:
        print(f"Contest with id={contest_id} does not exist.")
        return

    # 匯出 Submission
    submissions = Submission.objects.filter(contest=contest)
    submissions_data = []
    for s in submissions:
        submissions_data.append({
            "id": s.id,
            "submitted_by": s.submitted_by.username,
            "problem_id": s.problem.id,
            "source_code": s.source_code,
            "judge_compile_output": s.judge_compile_output,
            "judge_status_description": s.judge_status_description,
            "judge_status": s.judge_status,
            "submitted_at": s.submitted_at.isoformat(),
        })
    with open(f"contest_export_submissions_{contest_id}.json", "w", encoding="utf-8") as f:
        json.dump(submissions_data, f, ensure_ascii=False, indent=2)

    # 匯出 ContestRank
    ranks = ContestRank.objects.filter(contest=contest)
    ranks_data = []
    for r in ranks:
        ranks_data.append({
            "id": r.id,
            "submitted_by": r.submitted_by.username,
            "submission_count": r.submission_count,
            "accepted_count": r.accepted_count,
            "total_time": r.total_time,
            "submission_info": r.submission_info,
        })
    with open(f"contest_export_ranks_{contest_id}.json", "w", encoding="utf-8") as f:
        json.dump(ranks_data, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(submissions_data)} submissions and {len(ranks_data)} ranks for contest {contest_id}.")

if __name__ == "__main__":
    # 至少要有兩個元素（程式名稱 + contest_id）
    if len(sys.argv) < 2:
        print("Usage: python 1-export-contest-submission.py <contest_id>")
        sys.exit(1)
    contest_id = sys.argv[1]
    export_contest_data(contest_id)


