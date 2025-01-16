from django.db import models
from django.utils.timezone import now
from django.utils import timezone
import re
import base64


class MySysOptions(models.Model):

    option_name = models.TextField(null=True, blank=True)
    option_value = models.JSONField(null=True, default=list)

    def __str__(self):
        return f"{self.option_name}:{self.option_value}"


"""
# 預先寫入資料庫資料fixture
# python manage.py makemigrations app_manager
# python manage.py migrate app_manager
# python manage.py loaddata app_management/my-initial-sys-options.json
"""


class News(models.Model):
    message = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_permanent = models.BooleanField(
        default=True,
        help_text="永久顯示，否則會依據到期時間停止顯示",
    )

    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def __str__(self):
        return self.message


class Language(models.Model):

    name = models.CharField(max_length=15, default="")
    # Judge0 Extra CE identifier 需查閱其語言列表編號
    judge_id = models.IntegerField(default=0, help_text="Judge0 Extra CE identifier")
    is_default = models.BooleanField(default=False)  # 是否為內定的語言

    def __str__(self):
        return self.name


class ProblemCategory(models.Model):
    id = models.AutoField(primary_key=True)
    id_seq = models.CharField(
        max_length=15,
        default="10-10",
        help_text="顯示的順序，請依據章節主題的講授順序或難易度排列",
    )
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ("id_seq", "id")

    def __str__(self):
        return f"{self.name}"


# It's a better practice to use the class constants instead of the string literals
class ContestStatus(models.TextChoices):
    CONTEST_NOT_START = "NOT_STARTED", "未開始"
    CONTEST_ENDED = "ENDED", "已結束"
    CONTEST_UNDERWAY = "UNDERWAY", "進行中"


class JudgeStatus(models.IntegerChoices):
    IN_QUEUE = 1, "In Queue"
    PROCESSING = 2, "Processing"
    ACCEPTED = 3, "Accepted"
    WRONG_ANSWER = 4, "Wrong Answer"
    CPU_TIME_LIMIT_EXCEEDED = 5, "CPU Time Limit Exceeded"
    COMPILE_ERROR_1 = 6, "Compile Error 1"
    RUNTIME_ERROR_2 = 7, "Runtime Error 2"
    RUNTIME_ERROR_3 = 8, "Runtime Error 3"
    RUNTIME_ERROR_4 = 9, "Runtime Error 4"
    RUNTIME_ERROR_5 = 10, "Runtime Error 5"
    RUNTIME_ERROR_6 = 11, "Runtime Error 6"
    RUNTIME_ERROR_7 = 12, "Runtime Error 7"
    INTERNAL_ERROR = 13, "Internal Error"
    EXEC_FORMAT_ERROR = 14, "Exec Format Error"


"""
對應的訊息
[{"id":1,"description":"In Queue"},{"id":2,"description":"Processing"},{"id":3,"description":"Accepted"},{"id":4,"description":"Wrong Answer"},{"id":5,"description":"Time Limit Exceeded"},{"id":6,"description":"Compilation Error"},{"id":7,"description":"Runtime Error (SIGSEGV)"},{"id":8,"description":"Runtime Error (SIGXFSZ)"},{"id":9,"description":"Runtime Error (SIGFPE)"},{"id":10,"description":"Runtime Error (SIGABRT)"},{"id":11,"description":"Runtime Error (NZEC)"},{"id":12,"description":"Runtime Error (Other)"},{"id":13,"description":"Internal Error"},{"id":14,"description":"Exec Format Error"}]
"""


# 目前沒有使用
class ProblemDifficulty(models.TextChoices):
    BASIC = "BASIC", "基本"
    MEDIUM = "MEDIUM", "中等"
    DIFFICULT = "DIFFICULT", "稍難"


class SolutionReleasePolicy(models.TextChoices):
    NEVER = "NEVER", "不公布"
    IMMEDIATE = "IMMEDIATE", "立即公布"
    AFTER_CONTEST = "AFTER_CONTEST", "結束後公布"


class Contest(models.Model):

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    password = models.CharField(max_length=25, null=True, blank=True)  # no usage
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_visible = models.BooleanField(default=False)
    # is_password_protected = models.BooleanField(default=False) # no usage yet

    # for the display sequence
    display_seq = models.CharField(
        db_index=True, max_length=50, default="100-100-100"
    )  # for display order

    # problems (ManyToMany through ContestProblem)
    # 關聯的所有題目 透過中間表 ContestProblem 關聯 並且可以透過 related_name 反查
    # contest.problems.all() 可以取得所有的題目
    # problem.contests.all() 可以取得所有的比賽
    problems = models.ManyToManyField(
        "Problem", through="ContestProblem", related_name="contests"
    )

    # Add the new field using the class constants
    solution_release_policy = models.CharField(
        max_length=20,
        choices=SolutionReleasePolicy.choices,
        default=SolutionReleasePolicy.NEVER,
    )

    class Meta:
        ordering = ("-display_seq",)

    def __str__(self):
        return self.title

    def get_problems(self):
        return self.problems.all().order_by("-category")

    @property
    def status(self):
        if self.start_time > now():
            # 還没有開始
            return ContestStatus.CONTEST_NOT_START
        elif self.end_time < now():
            # 已經结束
            return ContestStatus.CONTEST_ENDED
        else:
            # 正在進行
            return ContestStatus.CONTEST_UNDERWAY

    #
    def status_label(self):
        return ContestStatus(self.status).label


def stringToBase64(src):
    return base64.b64encode(src.encode("utf-8")).decode("ascii")


class Problem(models.Model):

    # 章節主題
    categories = models.ManyToManyField(ProblemCategory, related_name="problems")
    # category = models.ForeignKey(ProblemCategory, on_delete=models.CASCADE)

    title = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    input_output_description = models.TextField(null=True, blank=True)
    std_input = models.TextField(null=True, blank=True)
    std_output = models.TextField(null=True, blank=True)
    sample_code = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    template = models.TextField(null=True, blank=True)
    # languages_1 = models.JSONField(default=list, null=True, blank=True)
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="problems",
        default=None,
        null=True,
    )

    # 新增的困難度欄位 尚未使用
    # difficulty = models.CharField(max_length=10, choices=ProblemDifficulty.choices, default=ProblemDifficulty.BASIC, null=True, blank=True)

    def get_test_cases(self):

        # 假設 std_in 使用 --- 分隔多組資料
        # 可以考題新增時候處理，不用在這裡處理
        # .replace('\r\n', '').replace('\n', '').replace('\r', '')

        # 假設 problem.std_input 是一個包含多個減號和換行符號分隔的字符串
        std_inputs = re.split(r"-{3,}(\r\n)", self.std_input)
        # 過濾掉空的元素
        std_inputs = [s for s in std_inputs if s.strip()]

        # 假設 problem.std_input 是一個包含多個減號分隔的字符串
        # split_input = re.split(r'-{3,}', problem.std_input)
        # std_inputs = problem.std_input.split('---\r\n')  # 這裡必須要如此切割，否則須要移除切割測資之後，第二個測資的最左側多一個換行符\r\n
        # std_outputs = problem.std_output.split('---\r\n')
        std_outputs = re.split(r"-{3,}(\r\n)", self.std_output)
        std_outputs = [s for s in std_outputs if s.strip()]

        test_case_list = []
        for idx in range(len(std_outputs)):
            if std_inputs:
                std_input = std_inputs[idx].strip()
            else:
                std_input = ""
            std_output = std_outputs[idx].lstrip(
                "\r\n"
            )  # 這裡要移除切割測資之後，第二個測資的最左側多一個換行符\r\n
            # logger.info(f"std_input:{std_input}")
            # logger.info(f"std_output:{std_output}")
            std_input = stringToBase64(std_input)
            std_output = stringToBase64(std_output)

            test_case_list.append(
                {
                    "stdin": std_input,  # 每組資料作為一個 stdin
                    "expected_output": std_output,  # 每組對應的預期輸出
                }
            )
        # logger.info(test_case_list)
        # v1.14版才會有多筆測試案例，請期待!
        # test_case_list =[{
        #     "stdin": stdin,
        #     "expected_output": expectedOutput
        # }]
        # test_case_list =[{
        #     "stdin": problem.std_input,
        #     "expected_output":problem.std_output
        # }]
        return test_case_list

    def default_data():
        return """
        //PREPEND BEGIN
        //PREPEND END
        //TEMPLATE BEGIN
        //TEMPLATE END
        //APPEND BEGIN
        //APPEND END"""

    def __str__(self):
        return self.title


class ContestProblem(models.Model):
    # id for the problem in contest
    id_prblm_in_contest = models.CharField(max_length=25, default="q1")
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.contest.title} (id:{self.problem.id},  seq_id:{self.id_prblm_in_contest})"

    class Meta:
        ordering = ("-id",)
