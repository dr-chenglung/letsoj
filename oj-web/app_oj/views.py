from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.timezone import now
from django.db.models import Q

from app_account.models import User
from app_management.models import MySysOptions, News
from app_management.models import Problem, Contest, ContestStatus, ContestProblem
from app_oj.models import Submission, ContestRank, JudgeStatus

import math
from django.utils import timezone
import markdown
import requests
import re
import base64
import json

import logging

logger = logging.getLogger(__name__)


def announcements(request):
    now = timezone.now()
    active_news = News.objects.filter(
        Q(is_permanent=True, start_time__lte=now)
        | Q(is_permanent=False, start_time__lte=now, end_time__gte=now)
    ).order_by(
        "-start_time"
    )  # Order by start_time descending
    return render(request, "app_oj/announcements.html", {"active_news": active_news})


def oj_about(request):
    return render(request, "app_oj/oj_about.html")


def learning_map(request):
    return render(request, "app_oj/learning_map.html")


def contest_list(request):

    contests = Contest.objects.filter(is_public=True)

    now = timezone.now()
    news_list = News.objects.filter(start_time__lte=now, end_time__gte=now)

    page = request.GET.get("page", 1)

    paginator = Paginator(contests, 7)
    try:
        contests = paginator.page(page)
    except PageNotAnInteger:
        contests = paginator.page(1)
    except EmptyPage:
        contests = paginator.page(paginator.num_pages)

    return render(
        request,
        "app_oj/contest_list.html",
        {"contests": contests, "news_list": news_list},
    )


@login_required(login_url="user_login")
def contest_detail(request, contest_pk):

    try:
        contest = Contest.objects.get(pk=contest_pk)
    except Contest.DoesNotExist:
        # raise Http404("Contest does not exist")
        return redirect("contest_list")

    contest_problems = ContestProblem.objects.filter(contest=contest).order_by(
        "id_prblm_in_contest"
    )
    # 以下3種寫法皆可??
    # problems = contest.problems.all().order_by("-category")
    # problems = contest.get_problems()
    # problems = Problem.objects.filter(contests__id__contains=contest.id).order_by("-created_at") #OK

    # 如果競賽還沒開始或是不公開就不可以查看，必須檢查! 否則有安全疑慮，可透過contest_pk看到考題
    if (
        not request.user.is_staff and contest.status is ContestStatus.CONTEST_NOT_START
    ) or not contest.is_public:
        return redirect("contest_list")

    try:
        contest_rank = ContestRank.objects.get(
            submitted_by=request.user, contest=contest
        )
    except ContestRank.DoesNotExist:
        # 還沒有submission
        contest_rank = None

    context = {
        "contest": contest,
        "contest_rank": contest_rank,
        "contest_problems": contest_problems,
    }
    return render(request, "app_oj/contest_detail.html", context)


@login_required(login_url="user_login")
def contest_problem_submit(request, contest_pk, problem_pk):

    # 貼上程式碼準備提交，只有GET模式，沒有POST模式。按下提交按鈕是透過Ajax來提交程式碼。
    # 若此題已經提交接受過了，則提交按鈕會disabled

    # 取得競賽，若不存在則返回到競賽列表頁面。
    # 防止入侵者通過 Http404 異常來推斷數據庫中是否存在該記錄。
    try:
        contest = Contest.objects.get(pk=contest_pk)
    except Contest.DoesNotExist:
        # raise Http404("Contest does not exist")
        return redirect("contest_list")
    # 注意: 如果競賽還沒開始或是不公開就不可以查看，必須檢查! 否則會考題洩漏!
    if (
        not request.user.is_staff and contest.status is ContestStatus.CONTEST_NOT_START
    ) or not contest.is_public:
        return redirect("contest_list")
    # 取得考題
    try:
        problem = Problem.objects.get(pk=problem_pk)
    except Problem.DoesNotExist:
        # raise Http404("Problem does not exist")
        return redirect("contest_list")
    # 檢查考題是否在此競賽中
    try:
        contest_problem = ContestProblem.objects.get(contest=contest, problem=problem)
    except ContestProblem.DoesNotExist:
        return redirect("contest_list")

    # problems = Problem.objects.filter(contests__id__contains=contest.id).order_by("-created_at")
    sys_options = {
        item.option_name: item.option_value for item in MySysOptions.objects.all()
    }
    # 提交的程式碼是否顯示(預防透過登入別人帳號查看答案)
    hide_submitted_code = sys_options["hide_submitted_code"] == "True"
    # hide_submitted_code字符串內容是 "False" 或 "True"，可以使用字典映射來安全地轉換這些字符串為布爾值，不可用eval
    try:
        # 已經有submission過了，需登入的考生才可以看到自己的submission
        submission = Submission.objects.get(
            submitted_by=request.user, contest=contest, problem=problem
        )
        #
        # logger.info("已經有submission過了")
        # logger.info(submission)
    except Submission.DoesNotExist:
        # 還沒有submission
        submission = None
        # logger.info("還沒有submission")

    # 設定可否觀看繳交答案
    # 暫時不可觀看繳交答案，避免抄襲，透過他人帳號進去看答案。
    # 競賽結束後才開放觀看
    # Todo: 繳交答案成功->不准看   不成功的程式碼->可以看  這樣比較合理。
    try:
        # 排行資訊contest rank
        contestRank = ContestRank.objects.get(
            submitted_by=request.user, contest=contest
        )
        submit_info = contestRank.submission_info.get(str(problem_pk))
        # submission不是空的，表示此題有提交過因此會有submit_info["is_ac"]是否成功的資訊
        # 有提交過，但是沒有contestRank??

        # if not contest.status == ContestStatus.CONTEST_ENDED:
        #     submission.source_code = ""
        # and submit_info is not None and submit_info["is_ac"] 應該不必要。 萬一submit_info沒有值，會噴錯
        # hide_submitted_code: AC之後，不可以看自己的提交紀錄，避免考試時帳號給他人，讓他人查看其答案。
        if (
            hide_submitted_code
            and contest.status != ContestStatus.CONTEST_ENDED
            and submit_info is not None
            and submit_info["is_ac"]
        ):
            submission.source_code = ""
    except ContestRank.DoesNotExist:
        contestRank = None

    # 檢查 solution_release_policy 和 contest.status
    if (
        contest.solution_release_policy == "AFTER_CONTEST"
        and contest.status == ContestStatus.CONTEST_ENDED
    ) or contest.solution_release_policy == "IMMEDIATE":
        # logger.info("可以看答案")
        pass
    else:
        # logger.info("不可以看答案")
        contest_problem.problem.sample_code = None

    # 此版本在後端渲染，比在前端渲染快速，但是須設定```區域的格式: fenced_code 與 顏色codehilite顯示
    contest_problem.problem.description = markdown.markdown(
        contest_problem.problem.description, extensions=["fenced_code", "codehilite"]
    )
    # logger.info( contest_problem.problem.description )

    contest_problem.problem.input_output_description = markdown.markdown(
        contest_problem.problem.input_output_description,
        extensions=["fenced_code", "codehilite"],
    )

    context = {
        "contest": contest,
        "submission": submission,
        "contest_problem": contest_problem,
    }

    return render(request, "app_oj/contest_problem_submit.html", context)


"""
使用非同步處理和輪詢的方式
這樣的設計確實有助於減輕後端伺服器的負擔，特別是當處理大量並行的請求時。以下是一些幫助減輕負擔的方式：
1. **異步處理：** 通過使用輪詢和非同步請求，後端不需要等待長時間的請求完成。相反，它可以立即回應請求，讓客戶端處於等待狀態，並在任務完成後更新。
2. **節省資源：** 在使用非同步處理的情況下，後端不需要保持與客戶端的連接或佔用伺服器資源。它可以立即處理其他請求或任務，從而更有效地使用資源。
3. **避免阻塞：** 如果使用了同步處理，伺服器將不得不等待任務完成後才能繼續處理其他請求。這將導致伺服器的阻塞，降低了伺服器的並發處理能力。
4. **增強用戶體驗：** 使用非同步處理，用戶可以立即收到部分回饋，例如 "任務已啟動" 的消息，這有助於提升用戶體驗，因為用戶不需要無休止地等待長時間的請求完成。
總的來說，通過使用非同步處理和輪詢，後端能夠更有效地處理並行請求，提高伺服器的效能和吞吐量，同時提供更好的用戶體驗。
"""


# For http version
judger_url = "http://server:2358/submissions/"  # judge0 server


def judge(sourceCode, stdin, expected_output, language_id):

    # Judger need to receive the following data
    judge0_payload = {
        "source_code": sourceCode,
        "language_id": language_id,  # 例如，Java語言
        "stdin": stdin,
        "expected_output": expected_output,
        # "test_cases": test_case_list,
    }
    # 將 test_cases 轉換為 JSON
    # judge0_payload = json.dumps(judge0_payload)
    # logger.info(judge0_payload)

    # 送給Judger執行 若發生例外，會被捕捉到
    try:
        # logger.info('Judger執行前')
        # response_post = requests.request("POST", judger_url, data=submitted_data)
        response_post = requests.request(
            "POST", judger_url + "?base64_encoded=true", data=judge0_payload
        )
        # logger.info('Judger執行後')
        # logger.info(response_post.text)

    except Exception as error:
        logger.error("Judger發生例外了!")
        logger.error(error)

    token = response_post.json()["token"]
    # print("呼叫!!取submissions取得token:",token)
    # response = {"token:",token}

    return token


"""
#  test_cases 結構
judge0_payload = {
    "source_code": "你的程式碼",
    "language_id": 50,  # 例如,C語言
    "test_cases": test_case_list
}
"""

#  Code Modified from: QingDao Online Judge
# @lru_cache(maxsize=100): This decorator caches up to 100 results of the parse_problem_template function. If the function is called again with the same arguments, the cached result is returned instead of recalculating it.
# lru stands for Least Recently Used. The lru_cache decorator in Python uses this caching strategy to store function results. When the cache reaches its maximum size, the least recently used items are discarded to make room for new ones.
# Caching: By caching the results, the function can quickly return the result for previously seen template_str values, improving efficiency.

from functools import lru_cache


@lru_cache(maxsize=100)
def parse_problem_template(template_str):

    if not template_str:
        return {"prepend": "", "template": "", "append": ""}

    # 注意://PREPEND BEGIN 後面接的空格或換行符號
    prepend = re.findall(r"//PREPEND BEGIN([\s\S]+?)//PREPEND END", template_str)
    # logger.info(prepend)
    template = re.findall(r"//TEMPLATE BEGIN([\s\S]+?)//TEMPLATE END", template_str)
    append = re.findall(r"//APPEND BEGIN([\s\S]+?)//APPEND END", template_str)
    return {
        "prepend": prepend[0] if prepend else "",
        "template": template[0] if template else "",
        "append": append[0] if append else "",
    }


def stringToBase64(src):
    return base64.b64encode(src.encode("utf-8")).decode("ascii")


def base64ToString(src):
    return base64.b64decode(src).decode("utf-8")

# Ajax呼叫提交到 Judger
@login_required(login_url="user_login")
@csrf_exempt
def submit_to_judger(request):

    # logger.info("提交考題.........")

    problem_id = request.POST.get("problem_id")
    contest_id = request.POST.get("contest_id")

    user = request.user
    contest = Contest.objects.get(id=contest_id)
    problem = Problem.objects.get(id=problem_id)
    # contest_problem = ContestProblem.objects.get(contest=contest, problem=problem)

    source_code = request.POST.get("source_code")
    # logger.info("取得source_code.........")

    # stdin = problem.std_input #
    # stdin = stringToBase64(problem.std_input) # 不能直接轉碼 當None type時會噴錯!

    # 這裡主要檢查 stdin is None 轉換編碼會噴錯
    # 要轉換編碼否則中文輸入會報錯
    # stdin = stringToBase64(stdin)

    # expectedOutput = problem.std_output #'5' #problem.expected_output
    # expectedOutput = stringToBase64(problem.std_output) #'5' #problem.expected_output

    judge_response_info = {}

    if contest.status == ContestStatus.CONTEST_ENDED and not request.user.is_staff:
        judge_response_info["result_status"] = "Expired"
        judge_response_info["judge_status_description"] = "比賽已經結束!"
        # logger.info("比賽已經結束.........")
        return JsonResponse(judge_response_info)
    # 讓管理者不受限制，可以提交做測試，加上以下條件: and not request.user.is_staff
    elif (
        contest.status == ContestStatus.CONTEST_NOT_START and not request.user.is_staff
    ):
        judge_response_info["result_status"] = "NotYetStart"
        judge_response_info["judge_status_description"] = "比賽尚未開始!"
        return JsonResponse(judge_response_info)

    # logger.info("檢查是否有submit過.........")
    # 檢查是否有submit過，若有，則更新時間與程式碼，若沒有，則新增一筆submission記錄提交
    try:
        # 看看有沒有提交過
        submission = Submission.objects.get(
            submitted_by=user, contest=contest, problem=problem
        )
        # logger.info("已經有submission過了")
        
        # 雖已經提交接受過了，仍讓使用者可以再次提交更完美的程式碼版本-->不再使用此功能了!
        # 提交按鈕已經在前端有管制，若已經提交過，則按鈕disabled，此處不必再次檢查，因為一定是新的或是尚未Accepted的情況 
        # 這裡的寫法是為了因應這種情況: Accepted之後，仍可以提交多次，但是只有最後一次的結果會被記錄，會影響排名
        # 前端已經有管制:<button type="button" id="submitMyCode" class="btn btn-primary" {% if contest.status == "ENDED" or submission.judge_status_description == "Accepted" %}disabled{% endif %}>提交程式碼...</button>
        # 讓管理者不受限制，可以提交做測試，加上以下條件: and not request.user.is_staff
        # if submission.judge_status == JudgeStatus.ACCEPTED and not request.user.is_staff:
        #     judge_response_info["result_status"] = "Accepted"
        #     judge_response_info["judge_status_description"] = "已經Accepted，別再送了!"
        #     return JsonResponse(judge_response_info)
        
        # 若已經有提交過，但是尚未Accepted，則更新提交時間與程式碼，繼續進行後面的提交程序
        # 記錄時間與程式碼
        submission.submitted_at = now()
        submission.source_code = source_code
        submission.save()

    # 首次提交:新增一筆新的submission，填入程式碼，與自動記錄現在時間。有無通過的細節在後面取得結果的函數中處理
    except Submission.DoesNotExist:
        submission = Submission.objects.create(
            submitted_by=user,
            contest=contest,
            problem=problem,
            source_code=source_code,
        )


    # 送給Judger執行: 不管是第一次提交還是再次提交(只有尚未Accepted情況，前面步驟已經排除Accepted情況)，都會送給Judger執行
    #### Java樣板
    # language = "Java"
    # if language in problem.template:

    # logger.info("problem.template")
    # logger.info(type(problem.template))
    # logger.info(problem.template)
    # logger.info(template)
    if problem.template.strip():
        template = parse_problem_template(problem.template)
        source_code = f"{template['prepend']}\n{source_code}\n{template['append']}"

    # logger.info(source_code)
    source_code = stringToBase64(source_code)

    # v1.14版才會有多筆測試案例，查看版本https://github.com/judge0/judge0
    # test_case_list =[{
    #     "stdin": stdin,
    #     "expected_output": expectedOutput
    # }]

    # 送給Judger執行
    judge_response_info = {}
    # 存放提交結果的 ID 列表
    submission_tokens = []
    judge_response_info["result_status"] = "SubmittingToJudgerOK"  # 處理中

    # logger.info("提交每組測資.........")
    test_cases = problem.get_test_cases()
    # 提交每組測資
    for test_case in test_cases:
        # 取得提交結果的 token
        try:
            # logger.info('丟給Judger!!!')
            # logger.info(test_case['stdin'])
            task_token = judge(
                source_code,
                test_case["stdin"],
                test_case["expected_output"],
                problem.language.judge_id,
            )
            submission_tokens.append(str(task_token))
        except Exception as error:
            judge_response_info["result_status"] = "SubmittingToJudgerError"  #
            logger.error("丟給Judger，發生例外了!")
            logger.error(error)
            break

    judge_response_info["task_token"] = submission_tokens
    
    # logger.info(judge_response_info)
    # result_status: 在前端會檢查狀態，判斷是否異常，還是正在處理中，以決定是否要繼續送出Ajax請求取得結果
    # judge_status_description: 顯示訊息在前端，讓使用者知道目前狀態
    # task_token: Ajax請求取得結果必須依據這個號碼取取得判題結果
    return JsonResponse(judge_response_info)


@login_required(login_url="user_login")
@csrf_exempt
def get_submission_result(request):
    # logger.info("取得提交結果.........")
    submission_tokens = eval(
        request.POST.get("task_token")
    )  # 字串格式轉換為list可用json.loads()
    # logger.info(f"tokens: {submission_tokens}")

    # 存放提交結果的 ID 列表
    judge_response_info = {}
    for task_token in submission_tokens:
        try:
            # 取結果
            # logger.info('取得Judger結果!!!')
            # logger.info(task_token)
            judge_result = requests.get(
                f"{judger_url}/{task_token}?base64_encoded=true"
            ).json()
            # print(response.json())
            # print(result.text)
            # logger.info(f"取得提交結果:{judge_result}")
        except Exception as error:
            logger.error("取得Judger結果，發生例外了!")
            logger.error(error)
            judge_response_info["result_status"] = "GetJudgerResultError"
            return JsonResponse(judge_response_info)

        status = judge_result["status"]["id"]
        judge_response_info["judge_status"] = status

        # 判斷是否還在排隊或處理中或是已經完成
        if status == JudgeStatus.IN_QUEUE or status == JudgeStatus.PROCESSING:
            # 還沒有獲得執行結果，則返回"JudgerInQueueOrProcessing"
            judge_response_info["result_status"] = "JudgerInQueueOrProcessing"
            return JsonResponse(judge_response_info)  # 直接回前端，持續呼叫取結果
        elif judge_result["status"]["id"] == JudgeStatus.ACCEPTED:
            # 答案正確
            # 必須所有都Acctepted，才算AC，繼續取得下一個結果
            judge_response_info["judge_compile_output"] = "通過~~全部測資都正確!"
            # 若是AC，則繼續取下一個結果，直到全部取完
            continue
        elif judge_result["status"]["id"] == JudgeStatus.WRONG_ANSWER:
            # 答案錯誤
            judge_response_info["judge_compile_output"] = (
                "未通過~~有部分或全部測資答案錯誤，請再仔細檢查程式碼!"
            )
            break
        elif judge_result["status"]["id"] == JudgeStatus.COMPILE_ERROR_1:
            # 編譯等錯誤 編號6
            if judge_result["compile_output"] is not None:
                judge_response_info["judge_compile_output"] = base64ToString(
                    judge_result["compile_output"]
                )  # 編譯錯誤，會有程式碼錯誤行，學生可檢查該行程式碼是否有語法錯誤!
            else:
                # 編譯錯誤，但是沒有編譯訊息(應該沒有這樣的情況才對)，避免這樣的情況發生轉換錯誤噴錯
                judge_response_info["judge_compile_output"] = (
                    "編譯錯誤，請檢查程式碼是否有語法錯誤!"
                )
            break
        elif judge_result["status"]["id"] == JudgeStatus.INTERNAL_ERROR:
            # 伺服器內部錯誤 編號
            judge_response_info["judge_compile_output"] = (
                "伺服器內部錯誤，請通報管理員，謝謝!"  #
            )
            break
        else:
            # 其他情況:執行期間錯誤Runtime Error, 此時judge_result['compile_output']是None
            judge_response_info["judge_compile_output"] = (
                "執行期間發生了錯誤，請檢查程式碼的邏輯是否有錯誤~"
            )
            break

    # JudgerSUCCESS成功完成判題(不管有沒有通過測資，Judger就是成功完成任務了!)，準備好資料回傳
    judge_response_info["result_status"] = "JudgerSUCCESS"
    judge_response_info["judge_status_description"] = judge_result["status"][
        "description"
    ]

    # 有獲得執行結果(除了前述JudgerInQueueOrProcessing情況回去前端持續呼叫之外，其他的結果明確，進行以下處理)
    problem_id = request.POST.get("problem_id")
    contest_id = request.POST.get("contest_id")

    user = request.user
    contest = Contest.objects.get(id=contest_id)
    problem = Problem.objects.get(id=problem_id)
    contest_problem = ContestProblem.objects.get(contest=contest, problem=problem)

    # logger.info(f"Submission更新,judge_response_info:{judge_response_info}")
    # 紀錄提交結果Submission
    Submission.objects.filter(
        submitted_by=user, contest=contest, problem=problem
    ).update(
        # **judge_response_info # 這樣會有問題，因為judge_response_info沒有某些key
        judge_compile_output=judge_response_info["judge_compile_output"],
        judge_status=judge_response_info["judge_status"],
        judge_status_description=judge_response_info["judge_status_description"],
    )

    submission = Submission.objects.get(
        submitted_by=user, contest=contest, problem=problem
    )
    # print(submission)

    # 紀錄排行資訊
    ### Update contest rank
    contestRank, sucess = ContestRank.objects.update_or_create(
        submitted_by=user, contest=contest
    )
    submit_info = contestRank.submission_info.get(str(problem_id))
    # 此題有提交過，需更新
    # contestRank.submission_count += 1
    if submit_info:
        contestRank.submission_count += 1
        # if not submit_info["is_ac"]: # 開啟此行:有提交過，無AC才更新
        # 否則不管是否有無AC，都會更新
        if judge_response_info["judge_status"] == JudgeStatus.ACCEPTED:
            if submit_info["is_ac"]:
                pass  # 有AC過，不必更新
            else:
                submit_info["is_ac"] = True
                contestRank.accepted_count += 1  # 這會用來計算分數平均完成時間排名

            # 可在此設定懲罰時間，錯一次完成時間加10分鐘 (取消此設定)
            submit_info["ac_time"] = (
                submission.submitted_at - contest.start_time
            ).total_seconds()
            contestRank.total_time = submit_info["ac_time"]
        elif (
            judge_response_info["judge_status"] != JudgeStatus.IN_QUEUE
            and judge_response_info["judge_status"] != JudgeStatus.PROCESSING
            and judge_response_info["judge_status"] != JudgeStatus.INTERNAL_ERROR
        ):
            # 發生其他錯誤 次數+1 若是內部錯誤，不計入錯誤次數
            submit_info["error_count"] += 1
            # 若是AC過，但是此次沒有AC，則減去AC次數
            if submit_info["is_ac"]:
                contestRank.accepted_count -= 1
            submit_info["is_ac"] = False

    # 第一次提交，新建submit_info
    else:
        contestRank.submission_count += 1
        submit_info = {
            "is_ac": False,
            "ac_time": 0,
            "error_count": 0,
            "qz_prblm_id": contest_problem.id_prblm_in_contest,
        }

        if judge_response_info["judge_status"] == JudgeStatus.ACCEPTED:
            contestRank.accepted_count += 1
            submit_info["is_ac"] = True
            submit_info["ac_time"] = (
                submission.submitted_at - contest.start_time
            ).total_seconds()
            # 總時間: 最後一次提交成功的時間 不要用累積時間
            contestRank.total_time = submit_info["ac_time"]

        elif (
            judge_response_info["judge_status"] != JudgeStatus.IN_QUEUE
            and judge_response_info["judge_status"] != JudgeStatus.PROCESSING
            and judge_response_info["judge_status"] != JudgeStatus.INTERNAL_ERROR
        ):
            submit_info["error_count"] = 1

    contestRank.submission_info[str(problem_id)] = submit_info
    contestRank.save()

    return JsonResponse(judge_response_info)


from collections import Counter


@login_required(login_url="user_login")
def get_contest_ranking(request, contest_id):
    contest = Contest.objects.get(pk=contest_id)

    # 如果競賽還沒開始或是不公開就不可以查看，必須檢查! 否則有安全疑慮
    if (
        not request.user.is_staff
        and contest.status is ContestStatus.CONTEST_NOT_START
        or not contest.is_public
    ):
        return redirect("contest_list")

    # 排除管理者的ranking
    staff = User.objects.filter(is_staff=True)
    contest_ranks = (
        ContestRank.objects.filter(contest=contest)
        .select_related("submitted_by")
        .exclude(submitted_by__in=staff)
        .order_by("-accepted_count", "total_time")
    )

    for userRecord in contest_ranks:
        if (
            userRecord.accepted_count != 0
        ):  # 有提交成功才有時間紀錄 若無時間紀錄在網頁會顯示"尚未提交"
            result = userRecord.total_time / 60 / userRecord.accepted_count
            userRecord.total_time = round(result, 1) if result < 10 else round(result)

            # q.total_time = round(q.total_time / 60 / q.accepted_count)
        # q.save() # 千萬不要存回資料庫 total_time原始的時間是秒,此處轉為分鐘,若未提交成功,total_time=0,網頁會判斷為'未完成'

    # from django.db.models import F
    # contest_ranks.update(total_time=F('total_time') / F('accepted_count'))

    # 計算答對題數的分布
    accepted_counts = contest_ranks.values_list("accepted_count", flat=True)
    grade_distribution = Counter(accepted_counts)

    # 計算每題答對人數的分布 (只計算 is_ac 為 True 的情況)
    problem_ids_ac = []
    for rank in contest_ranks:
        for submission in rank.submission_info.values():
            # logger.info(submission)
            if submission.get("is_ac"):
                problem_ids_ac.append(submission.get("qz_prblm_id"))

    problem_distribution_ac = Counter(problem_ids_ac)
    # 依據題號排序
    sorted_problem_distribution_ac = sorted(problem_distribution_ac.items())
    # 依據答對人數排序
    # sorted_problem_distribution_ac = sorted(problem_distribution_ac.items(), key=lambda x: x[1], reverse=True)

    content = {
        "contest_ranks": contest_ranks,
        "contest": contest,
        "grade_distribution": json.dumps(dict(grade_distribution)),
        "problem_distribution": json.dumps(dict(sorted_problem_distribution_ac)),
    }

    return render(request, "app_oj/contest_ranking.html", content)


@login_required(login_url="user_login")
def user_contests_summary(request):

    user = request.user
    attended_contest_ranks = ContestRank.objects.filter(submitted_by=user).order_by(
        "-contest__display_seq"
    )

    # 比對哪個該參加的公開競賽沒有參加
    all_public_contests = Contest.objects.filter(is_public=True)

    # # 获取用户参加过的 contest 列表
    # attended_contest_ids = attended_contest_ranks .values_list('contest_id', flat=True)
    # logger.info(attended_contest_ids)

    # # 获取所有未参加的 contests
    # contests_not_attended = all_public_contests.exclude(id__in=attended_contest_ids)
    # logger.info(contests_not_attended)

    # 假设 all_public_contests 和 attended_contests 都是查询集 (QuerySet)
    contests_not_attended = all_public_contests.exclude(
        id__in=attended_contest_ranks.values_list("contest__id", flat=True)
    )

    # 排除管理者的ranking
    staff = User.objects.filter(is_staff=True)

    contests_info = []
    for rank in attended_contest_ranks:
        contest = rank.contest
        contest_problems_count = ContestProblem.objects.filter(contest=contest).count()

        # 查詢比賽資料
        all_users_contest_ranks = (
            ContestRank.objects.filter(contest=contest)
            .select_related("submitted_by")
            .exclude(submitted_by__in=staff)
            .order_by("-accepted_count", "total_time")
        )

        # 計算得分數
        score = math.ceil(100 * (rank.accepted_count / contest_problems_count))

        user_rank = None
        average_time = 0
        if (
            rank.accepted_count != 0
        ):  # 有提交成功才有時間紀錄 若無時間紀錄在網頁會顯示"尚未提交"
            # 計算平均時間
            result = rank.total_time / 60 / rank.accepted_count
            average_time = round(result, 1) if result < 10 else round(result)

            # 計算排名
            for index, rank in enumerate(all_users_contest_ranks, start=1):
                if rank.submitted_by == request.user:
                    user_rank = index
                    break

        contest_info = {
            "contest": contest,
            "score": score,
            "accepted_count": rank.accepted_count,
            "problem_count": contest_problems_count,
            "submission_count": rank.submission_count,
            "user_rank": user_rank,
            "average_time": average_time,
        }
        contests_info.append(contest_info)

    context = {
        "contests_info": contests_info,
        "contests_not_attended": contests_not_attended,
    }
    for contest in contests_not_attended:
        contest_info = {
            "contest": contest,
            "score": "未參加",
            "accepted_count": "-",
            "problem_count": "-",
            "submission_count": "-",
            "user_rank": "-",
            "average_time": "-",
        }
        contests_info.append(contest_info)
    # Sort contests_info by contest.display_seq descending
    contests_info.sort(key=lambda x: x["contest"].display_seq, reverse=True)

    return render(request, "app_oj/user_contests_summary.html", context)
