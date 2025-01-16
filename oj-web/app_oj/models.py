from django.db import models
from django.conf import settings
from django.utils.timezone import now
import re
import base64

from app_account.models import User
from django.utils import timezone

from app_management.models import Problem, Contest


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


class Submission(models.Model):

    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)  # 目前版本不可為空值
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    source_code = models.TextField()

    ## 狀態與compiled output錯誤訊息 可以合併一起!
    judge_compile_output = models.TextField(null=True, blank=True)
    judge_status_description = models.CharField(max_length=20)
    judge_status = models.IntegerField(db_index=True, default=JudgeStatus.IN_QUEUE)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submitted_by", "contest", "problem"], name="unique_submission"
            )
        ]
        ordering = ("-submitted_at",)

    def __str__(self):
        return f"Submission by {self.submitted_by} for problem {self.problem.id} in contest {self.contest.id}"


class ContestRank(models.Model):

    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)

    submission_count = models.IntegerField(default=0)
    accepted_count = models.IntegerField(default=0)
    # total_time is only for ACM contest, total_time =  ac time + none-ac times * 20 * 60
    total_time = models.IntegerField(default=0)

    ## 包含題目與答題詳情----
    # {"23": {"is_ac": True, "ac_time": 8999, "error_number": 2}}
    # key is problem id
    submission_info = models.JSONField(default=dict)

    class Meta:
        pass
        # db_table = "contest_rank"
        # unique_together = (("submitted_by", "contest"),)

    def __str__(self):
        # return self.id
        return f"Rank of {self.submitted_by} in contest {self.contest.id}"


# Judge0 github for more information
"""

class JudgeStatus:
    IN_QUEUE = 1
    PROCESSING = 2
    ACCEPTED = 3
    WRONG_ANSWER = 4
    CPU_TIME_LIMIT_EXCEEDED = 5
    COMPILE_ERROR_1 = 6
    RUNTIME_ERROR_2 = 7
    RUNTIME_ERROR_3 = 8
    RUNTIME_ERROR_4 = 9
    RUNTIME_ERROR_5 = 10
    RUNTIME_ERROR_6 = 11
    RUNTIME_ERROR_7 = 12
    INTERNAL_ERROR = 13
    EXEC_FORMAT_ERROR = 14
"""


"""
Judge0 CE Extra:
[
    {
        "id": 11,
        "name": "Bosque (latest)"
    },
    {
        "id": 3,
        "name": "C3 (latest)"
    },
    {
        "id": 1,
        "name": "C (Clang 10.0.1)"
    },
    {
        "id": 2,
        "name": "C++ (Clang 10.0.1)"
    },
    {
        "id": 13,
        "name": "C (Clang 9.0.1)"
    },
    {
        "id": 14,
        "name": "C++ (Clang 9.0.1)"
    },
    {
        "id": 22,
        "name": "C# (Mono 6.12.0.122)"
    },
    {
        "id": 21,
        "name": "C# (.NET Core SDK 3.1.406)"
    },
    {
        "id": 15,
        "name": "C++ Test (Clang 10.0.1, Google Test 1.8.1)"
    },
    {
        "id": 12,
        "name": "C++ Test (GCC 8.4.0, Google Test 1.8.1)"
    },
    {
        "id": 23,
        "name": "C# Test (.NET Core SDK 3.1.406, NUnit 3.12.0)"
    },
    {
        "id": 24,
        "name": "F# (.NET Core SDK 3.1.406)"
    },
    {
        "id": 4,
        "name": "Java (OpenJDK 14.0.1)"
    },
    {
        "id": 5,
        "name": "Java Test (OpenJDK 14.0.1, JUnit Platform Console Standalone 1.6.2)"
    },
    {
        "id": 6,
        "name": "MPI (OpenRTE 3.1.3) with C (GCC 8.4.0)"
    },
    {
        "id": 7,
        "name": "MPI (OpenRTE 3.1.3) with C++ (GCC 8.4.0)"
    },
    {
        "id": 8,
        "name": "MPI (OpenRTE 3.1.3) with Python (3.7.7)"
    },
    {
        "id": 89,
        "name": "Multi-file program"
    },
    {
        "id": 9,
        "name": "Nim (stable)"
    },
    {
        "id": 10,
        "name": "Python for ML (3.7.7)"
    },
    {
        "id": 20,
        "name": "Visual Basic.Net (vbnc 0.0.0.5943)"
    }
]
"""

"""
Judge0 CE:
[
    {
        "id": 45,
        "name": "Assembly (NASM 2.14.02)"
    },
    {
        "id": 46,
        "name": "Bash (5.0.0)"
    },
    {
        "id": 47,
        "name": "Basic (FBC 1.07.1)"
    },
    {
        "id": 75,
        "name": "C (Clang 7.0.1)"
    },
    {
        "id": 76,
        "name": "C++ (Clang 7.0.1)"
    },
    {
        "id": 48,
        "name": "C (GCC 7.4.0)"
    },
    {
        "id": 52,
        "name": "C++ (GCC 7.4.0)"
    },
    {
        "id": 49,
        "name": "C (GCC 8.3.0)"
    },
    {
        "id": 53,
        "name": "C++ (GCC 8.3.0)"
    },
    {
        "id": 50,
        "name": "C (GCC 9.2.0)"
    },
    {
        "id": 54,
        "name": "C++ (GCC 9.2.0)"
    },
    {
        "id": 86,
        "name": "Clojure (1.10.1)"
    },
    {
        "id": 51,
        "name": "C# (Mono 6.6.0.161)"
    },
    {
        "id": 77,
        "name": "COBOL (GnuCOBOL 2.2)"
    },
    {
        "id": 55,
        "name": "Common Lisp (SBCL 2.0.0)"
    },
    {
        "id": 56,
        "name": "D (DMD 2.089.1)"
    },
    {
        "id": 57,
        "name": "Elixir (1.9.4)"
    },
    {
        "id": 58,
        "name": "Erlang (OTP 22.2)"
    },
    {
        "id": 44,
        "name": "Executable"
    },
    {
        "id": 87,
        "name": "F# (.NET Core SDK 3.1.202)"
    },
    {
        "id": 59,
        "name": "Fortran (GFortran 9.2.0)"
    },
    {
        "id": 60,
        "name": "Go (1.13.5)"
    },
    {
        "id": 88,
        "name": "Groovy (3.0.3)"
    },
    {
        "id": 61,
        "name": "Haskell (GHC 8.8.1)"
    },
    {
        "id": 62,
        "name": "Java (OpenJDK 13.0.1)"
    },
    {
        "id": 63,
        "name": "JavaScript (Node.js 12.14.0)"
    },
    {
        "id": 78,
        "name": "Kotlin (1.3.70)"
    },
    {
        "id": 64,
        "name": "Lua (5.3.5)"
    },
    {
        "id": 89,
        "name": "Multi-file program"
    },
    {
        "id": 79,
        "name": "Objective-C (Clang 7.0.1)"
    },
    {
        "id": 65,
        "name": "OCaml (4.09.0)"
    },
    {
        "id": 66,
        "name": "Octave (5.1.0)"
    },
    {
        "id": 67,
        "name": "Pascal (FPC 3.0.4)"
    },
    {
        "id": 85,
        "name": "Perl (5.28.1)"
    },
    {
        "id": 68,
        "name": "PHP (7.4.1)"
    },
    {
        "id": 43,
        "name": "Plain Text"
    },
    {
        "id": 69,
        "name": "Prolog (GNU Prolog 1.4.5)"
    },
    {
        "id": 70,
        "name": "Python (2.7.17)"
    },
    {
        "id": 71,
        "name": "Python (3.8.1)"
    },
    {
        "id": 80,
        "name": "R (4.0.0)"
    },
    {
        "id": 72,
        "name": "Ruby (2.7.0)"
    },
    {
        "id": 73,
        "name": "Rust (1.40.0)"
    },
    {
        "id": 81,
        "name": "Scala (2.13.2)"
    },
    {
        "id": 82,
        "name": "SQL (SQLite 3.27.2)"
    },
    {
        "id": 83,
        "name": "Swift (5.2.3)"
    },
    {
        "id": 74,
        "name": "TypeScript (3.7.4)"
    },
    {
        "id": 84,
        "name": "Visual Basic.Net (vbnc 0.0.0.5943)"
    }
]
"""
