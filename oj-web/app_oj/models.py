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
        # 刻意設計：(submitted_by, contest, problem) 唯一，每位學生每題只保留「最後一次」提交。
        # 重複提交會覆蓋原本的 source_code 與判題狀態，不保留完整提交歷史。
        # 對課堂用途足夠；若日後需要稽核完整提交歷程，須移除此約束並改為每次提交新增一筆，
        # 同時將各處 Submission.objects.get(submitted_by, contest, problem) 改為取最新一筆。
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
    # {"23": {"is_ac": True, "ac_time": 8999, "error_count": 2}}
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
Judge0 CE:

43	Plain Text
44	Executable
45	Assembly (NASM 2.14.02)
46	Bash (5.0.0)
47	Basic (FBC 1.07.1)
48	C (GCC 7.4.0)
49	C (GCC 8.3.0)
50	C (GCC 9.2.0)
51	C# (Mono 6.6.0.161)
52	C++ (GCC 7.4.0)
53	C++ (GCC 8.3.0)
54	C++ (GCC 9.2.0)
55	Common Lisp (SBCL 2.0.0)
56	D (DMD 2.089.1)
57	Elixir (1.9.4)
58	Erlang (OTP 22.2)
59	Fortran (GFortran 9.2.0)
60	Go (1.13.5)
61	Haskell (GHC 8.8.1)
62	Java (OpenJDK 13.0.1)
63	JavaScript (Node.js 12.14.0)
64	Lua (5.3.5)
65	OCaml (4.09.0)
66	Octave (5.1.0)
67	Pascal (FPC 3.0.4)
68	PHP (7.4.1)
69	Prolog (GNU Prolog 1.4.5)
70	Python (2.7.17)
71	Python (3.8.1)
72	Ruby (2.7.0)
73	Rust (1.40.0)
74	TypeScript (3.7.4)
75	C (Clang 7.0.1)
76	C++ (Clang 7.0.1)
77	COBOL (GnuCOBOL 2.2)
78	Kotlin (1.3.70)
79	Objective-C (Clang 7.0.1)
80	R (4.0.0)
81	Scala (2.13.2)
82	SQL (SQLite 3.27.2)
83	Swift (5.2.3)
84	Visual Basic.Net (vbnc 0.0.0.5943)
85	Perl (5.28.1)
86	Clojure (1.10.1)
87	F# (.NET Core SDK 3.1.202)
88	Groovy (3.0.3)
89	Multi-file program


官網商用版本:
45	Assembly (NASM 2.14.02)
46	Bash (5.0.0)
47	Basic (FBC 1.07.1)
104	C (Clang 18.1.8)
110	C (Clang 19.1.7)
75	C (Clang 7.0.1)
103	C (GCC 14.1.0)
48	C (GCC 7.4.0)
49	C (GCC 8.3.0)
50	C (GCC 9.2.0)
76	C++ (Clang 7.0.1)
105	C++ (GCC 14.1.0)
52	C++ (GCC 7.4.0)
53	C++ (GCC 8.3.0)
54	C++ (GCC 9.2.0)
51	C# (Mono 6.6.0.161)
86	Clojure (1.10.1)
77	COBOL (GnuCOBOL 2.2)
55	Common Lisp (SBCL 2.0.0)
56	D (DMD 2.089.1)
90	Dart (2.19.2)
57	Elixir (1.9.4)
58	Erlang (OTP 22.2)
44	Executable
87	F# (.NET Core SDK 3.1.202)
59	Fortran (GFortran 9.2.0)
60	Go (1.13.5)
95	Go (1.18.5)
106	Go (1.22.0)
107	Go (1.23.5)
88	Groovy (3.0.3)
61	Haskell (GHC 8.8.1)
62	Java (OpenJDK 13.0.1)
91	Java (JDK 17.0.6)
96	JavaFX (JDK 17.0.6, OpenJFX 22.0.2)
63	JavaScript (Node.js 12.14.0)
93	JavaScript (Node.js 18.15.0)
97	JavaScript (Node.js 20.17.0)
102	JavaScript (Node.js 22.08.0)
78	Kotlin (1.3.70)
111	Kotlin (2.1.10)
64	Lua (5.3.5)
89	Multi-file program
79	Objective-C (Clang 7.0.1)
65	OCaml (4.09.0)
66	Octave (5.1.0)
67	Pascal (FPC 3.0.4)
85	Perl (5.28.1)
68	PHP (7.4.1)
98	PHP (8.3.11)
43	Plain Text
69	Prolog (GNU Prolog 1.4.5)
70	Python (2.7.17)
71	Python (3.8.1)
92	Python (3.11.2)
100	Python (3.12.5)
109	Python (3.13.2)
113	Python (3.14.0)
80	R (4.0.0)
99	R (4.4.1)
72	Ruby (2.7.0)
73	Rust (1.40.0)
108	Rust (1.85.0)
81	Scala (2.13.2)
112	Scala (3.4.2)
82	SQL (SQLite 3.27.2)
83	Swift (5.2.3)
74	TypeScript (3.7.4)
94	TypeScript (5.0.3)
101	TypeScript (5.6.2)
"""
