import io
import json
from datetime import timedelta

import openpyxl
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.utils import timezone

from app_account.models import LoginHistory, User
from app_management.models import Contest, Language, Problem
from app_oj.models import ContestRank, Submission


class NoLoginUsersClassFilterTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("teacher", password="pw", is_staff=True, user_class="T")
        self.a1 = User.objects.create_user("a1", password="pw", user_class="1A")
        self.a2 = User.objects.create_user("a2", password="pw", user_class="1A")
        self.b1 = User.objects.create_user("b1", password="pw", user_class="2B")
        self.client = Client()
        self.client.login(username="teacher", password="pw")

    def test_class_dropdown_lists_student_classes_only(self):
        resp = self.client.get("/manage/manage_contest/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context["class_list"]), ["1A", "2B"])
        self.assertContains(resp, '<option value="1A">1A</option>', html=True)
        self.assertNotContains(resp, '<option value="T">T</option>', html=True)

    def test_filter_by_class_lists_absent_students_of_that_class(self):
        LoginHistory.objects.create(user=self.a1, ip="192.168.0.11")
        resp = self.client.post("/manage/get_no_login_users/", {"query_class": "1A", "query_time": ""})
        usernames = [u["username"] for u in resp.json()["no_login_users"]]
        self.assertEqual(usernames, ["a2"])

    def test_all_classes_when_no_class_selected(self):
        LoginHistory.objects.create(user=self.a1, ip="192.168.0.11")
        resp = self.client.post("/manage/get_no_login_users/", {"query_class": "", "query_time": ""})
        usernames = sorted(u["username"] for u in resp.json()["no_login_users"])
        self.assertEqual(usernames, ["a2", "b1"])


class NoSubmissionUsersTests(TestCase):
    """查詢「已登入但在指定考試中尚未提交」的學生"""

    def setUp(self):
        now = timezone.now()
        self.teacher = User.objects.create_user("teacher", password="pw", is_staff=True, user_class="T")
        self.a1 = User.objects.create_user("a1", password="pw", user_class="1A")
        self.a2 = User.objects.create_user("a2", password="pw", user_class="1A")
        self.a3 = User.objects.create_user("a3", password="pw", user_class="1A")
        self.b1 = User.objects.create_user("b1", password="pw", user_class="2B")
        self.exam = Contest.objects.create(
            title="期中考", is_public=True,
            start_time=now - timedelta(minutes=30), end_time=now + timedelta(minutes=90),
        )
        self.other = Contest.objects.create(
            title="練習", is_public=True,
            start_time=now - timedelta(days=1), end_time=now - timedelta(hours=20),
        )
        self.problem = Problem.objects.create(title="p1")
        self.client = Client()
        self.client.login(username="teacher", password="pw")

    def _submit(self, user, contest):
        Submission.objects.create(
            submitted_by=user, contest=contest, problem=self.problem,
            source_code="print(1)", judge_status_description="In Queue",
        )

    def _query(self, query_class="", contest=None):
        resp = self.client.post("/manage/get_no_submission_users/", {
            "query_class": query_class, "query_time": "",
            "contest_id": (contest or self.exam).pk,
        })
        self.assertEqual(resp.status_code, 200)
        return resp.json()["no_submission_users"]

    def test_logged_in_without_submission_is_listed_with_last_ip(self):
        LoginHistory.objects.create(user=self.a1, ip="192.168.0.11")
        users = self._query("1A")
        self.assertEqual([u["username"] for u in users], ["a1"])
        self.assertEqual(users[0]["last_login_ip"], "192.168.0.11")

    def test_student_who_submitted_in_this_contest_is_excluded(self):
        LoginHistory.objects.create(user=self.a1, ip="192.168.0.11")
        LoginHistory.objects.create(user=self.a2, ip="192.168.0.12")
        self._submit(self.a2, self.exam)
        self.assertEqual([u["username"] for u in self._query("1A")], ["a1"])

    def test_submission_in_other_contest_does_not_count(self):
        LoginHistory.objects.create(user=self.a1, ip="192.168.0.11")
        self._submit(self.a1, self.other)
        self.assertEqual([u["username"] for u in self._query("1A")], ["a1"])

    def test_not_logged_in_students_are_not_listed(self):
        # a3 沒登入，屬於「未登入」名單，不應出現在這裡
        LoginHistory.objects.create(user=self.a1, ip="192.168.0.11")
        self.assertNotIn("a3", [u["username"] for u in self._query("1A")])

    def test_all_classes_when_no_class_selected(self):
        LoginHistory.objects.create(user=self.a1, ip="192.168.0.11")
        LoginHistory.objects.create(user=self.b1, ip="192.168.0.21")
        self.assertEqual(sorted(u["username"] for u in self._query("")), ["a1", "b1"])

    def test_missing_contest_returns_400(self):
        resp = self.client.post("/manage/get_no_submission_users/", {"query_class": "", "query_time": ""})
        self.assertEqual(resp.status_code, 400)

    def test_requires_staff(self):
        client = Client()
        client.login(username="a1", password="pw")
        resp = client.post("/manage/get_no_submission_users/", {"contest_id": self.exam.pk})
        self.assertNotEqual(resp.status_code, 200)


class RecentContestDropdownTests(TestCase):
    """考試下拉選單：只列近期公開的考試，進行中的排最前面"""

    def setUp(self):
        now = timezone.now()
        self.teacher = User.objects.create_user("teacher", password="pw", is_staff=True)

        def make(title, start, end, public=True):
            return Contest.objects.create(title=title, is_public=public, start_time=now + start, end_time=now + end)

        self.ended_recent = make("上週考試", -timedelta(days=7), -timedelta(days=7) + timedelta(hours=2))
        self.underway = make("進行中", -timedelta(minutes=30), timedelta(minutes=90))
        self.upcoming = make("明天考試", timedelta(days=1), timedelta(days=1, hours=2))
        self.ended_old = make("很久以前", -timedelta(days=60), -timedelta(days=60) + timedelta(hours=2))
        self.private = make("未公開", -timedelta(minutes=10), timedelta(minutes=50), public=False)
        self.client = Client()
        self.client.login(username="teacher", password="pw")

    def test_lists_recent_public_contests_with_underway_first(self):
        resp = self.client.get("/manage/manage_contest/")
        titles = [c.title for c in resp.context["contest_list"]]
        self.assertEqual(titles, ["進行中", "明天考試", "上週考試"])
        # 進行中的考試是第一個選項(瀏覽器預設選取)，並標示【進行中】
        html = resp.content.decode()
        first_option = html.split('id="queryContest"', 1)[1].split("</option>", 1)[0]
        self.assertIn(f'value="{self.underway.pk}"', first_option)
        self.assertIn("【進行中】進行中", first_option)


class ImportResetsPkSequenceTests(TestCase):
    """
    匯入功能會沿用來源的編號寫入資料庫，PostgreSQL 的序號不會跟著前進。
    匯入後必須把序號重設到最大編號，否則之後在網頁上新增會撞號(duplicate key)。
    每個測試都先探出「序號下一個會給的編號」，再以這個編號匯入，最後確認一般新增仍能成功。
    """

    def setUp(self):
        self.teacher = User.objects.create_user("teacher", password="pw", is_staff=True)
        self.student = User.objects.create_user("s1", password="pw")
        self.java = Language.objects.create(name="Java", judge_id=62)
        self.client = Client()
        self.client.login(username="teacher", password="pw")

    @staticmethod
    def _next_id(model, **fields):
        probe = model.objects.create(**fields)
        next_id = probe.pk + 1
        probe.delete()
        return next_id

    def test_excel_problem_import_then_create_problem(self):
        new_id = self._next_id(Problem, title="probe")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["id", "title", "description", "std_input", "std_output", "template", "sample_code", "language", "categories"])
        ws.append([new_id, "匯入的題目", "d", "1", "1", "", "", "Java", "數學運算"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        buf.name = "problems.xlsx"
        self.client.post("/manage/import_problems_from_excel/", {"excel_file": buf})
        self.assertTrue(Problem.objects.filter(pk=new_id, title="匯入的題目").exists())

        created = Problem.objects.create(title="匯入後在網頁新增")
        self.assertGreater(created.pk, new_id)

    def test_contest_import_then_create_contest_and_problem(self):
        new_problem_id = self._next_id(Problem, title="probe")
        new_contest_id = self._next_id(Contest, title="probe")
        files = {
            "contest_metadata_file": json.dumps({
                "id": new_contest_id, "title": "匯入的競賽", "description": "",
                "start_time": None, "end_time": None, "is_public": False,
                "is_weighted_ranking": False, "display_seq": "115-1-w06",
                "solution_release_policy": "NEVER",
            }),
            "problems_file": json.dumps([{
                "id": new_problem_id, "title": "匯入的題目", "description": "d",
                "std_input": "1", "std_output": "1", "sample_code": "", "template": "",
                "language": "Java", "categories": ["數學運算"],
            }]),
            "contest_problems_file": json.dumps([{"problem_id": new_problem_id, "id_prblm_in_contest": "q1"}]),
        }
        upload = {k: SimpleUploadedFile(f"{k}.json", v.encode("utf-8")) for k, v in files.items()}
        self.client.post("/manage/import_contest_and_problems/", upload)
        self.assertTrue(Contest.objects.filter(pk=new_contest_id).exists())
        self.assertTrue(Problem.objects.filter(pk=new_problem_id).exists())

        self.assertGreater(Problem.objects.create(title="新增題目").pk, new_problem_id)
        self.assertGreater(Contest.objects.create(title="新增競賽").pk, new_contest_id)


class ImportSubmissionsTests(TestCase):
    """
    匯入提交紀錄與排名：一律用「學生+競賽+題目」(排名用「學生+競賽」)比對，不沿用來源的 id。
    流程是正式站整個複製到考試站 → 考試 → 把考試站的提交匯回正式站，
    兩台伺服器各自產生的新提交 id 會重疊，用 id 比對會把正式站其他作業的提交蓋掉。
    同一學生同一題兩邊都有時，以匯入的考試站資料為準。
    """

    def setUp(self):
        self.teacher = User.objects.create_user("teacher", password="pw", is_staff=True)
        self.s1 = User.objects.create_user("s1", password="pw")
        self.s2 = User.objects.create_user("s2", password="pw")
        self.exam = Contest.objects.create(title="考試")
        self.homework = Contest.objects.create(title="作業")
        self.p1 = Problem.objects.create(title="p1")
        self.p2 = Problem.objects.create(title="p2")
        self.client = Client()
        self.client.login(username="teacher", password="pw")

    def _import(self, submissions, ranks):
        files = {"submissions_file": submissions, "ranks_file": ranks}
        upload = {k: SimpleUploadedFile(f"{k}.json", json.dumps(v).encode("utf-8")) for k, v in files.items()}
        return self.client.post("/manage/import_submissions/", upload)

    def _sub(self, sid, username, problem, code, status=3):
        return {
            "id": sid, "contest_id": self.exam.pk, "submitted_by": username, "problem_id": problem.pk,
            "source_code": code, "judge_compile_output": "", "judge_status_description": "Accepted",
            "judge_status": status, "submitted_at": "2026-10-14T08:00:00+00:00",
        }

    def _rank(self, rid, username, accepted):
        return {"id": rid, "submitted_by": username, "submission_count": 1, "accepted_count": accepted,
                "total_time": 0, "submission_info": {}}

    def test_same_id_on_other_homework_is_not_overwritten(self):
        # 正式站在考試期間有人交作業，id 和考試站的新提交重疊
        homework_sub = Submission.objects.create(
            submitted_by=self.s2, contest=self.homework, problem=self.p2,
            source_code="作業程式碼", judge_status_description="Accepted", judge_status=3,
        )
        homework_rank = ContestRank.objects.create(submitted_by=self.s2, contest=self.homework, accepted_count=1)

        self._import([self._sub(homework_sub.pk, "s1", self.p1, "考試程式碼")],
                     [self._rank(homework_rank.pk, "s1", 1)])

        homework_sub.refresh_from_db()
        self.assertEqual((homework_sub.submitted_by, homework_sub.contest, homework_sub.source_code),
                         (self.s2, self.homework, "作業程式碼"))
        homework_rank.refresh_from_db()
        self.assertEqual((homework_rank.submitted_by, homework_rank.contest), (self.s2, self.homework))

        exam_sub = Submission.objects.get(submitted_by=self.s1, contest=self.exam, problem=self.p1)
        self.assertEqual(exam_sub.source_code, "考試程式碼")
        # 提交時間要保留考試當時的時間，不能變成匯入的時間
        self.assertEqual(exam_sub.submitted_at.isoformat(), "2026-10-14T08:00:00+00:00")
        self.assertNotEqual(exam_sub.pk, homework_sub.pk)
        self.assertTrue(ContestRank.objects.filter(submitted_by=self.s1, contest=self.exam).exists())

    def test_existing_exam_record_is_replaced_by_imported_one(self):
        # 同一學生同一場同一題兩邊都有 → 以考試站(匯入檔)為準
        Submission.objects.create(
            submitted_by=self.s1, contest=self.exam, problem=self.p1,
            source_code="正式站上的舊程式碼", judge_status_description="Wrong Answer", judge_status=4,
        )
        ContestRank.objects.create(submitted_by=self.s1, contest=self.exam, accepted_count=0)

        self._import([self._sub(99999, "s1", self.p1, "考試站的程式碼")], [self._rank(99999, "s1", 1)])

        subs = Submission.objects.filter(submitted_by=self.s1, contest=self.exam, problem=self.p1)
        self.assertEqual(subs.count(), 1)
        self.assertEqual((subs[0].source_code, subs[0].judge_status), ("考試站的程式碼", 3))
        ranks = ContestRank.objects.filter(submitted_by=self.s1, contest=self.exam)
        self.assertEqual([r.accepted_count for r in ranks], [1])

    def test_reimport_same_file_does_not_duplicate(self):
        subs = [self._sub(70001, "s1", self.p1, "a"), self._sub(70002, "s1", self.p2, "b")]
        ranks = [self._rank(70001, "s1", 2)]
        self._import(subs, ranks)
        self._import(subs, ranks)
        self.assertEqual(Submission.objects.filter(contest=self.exam).count(), 2)
        self.assertEqual(ContestRank.objects.filter(contest=self.exam).count(), 1)

    def test_imported_ids_are_not_used_so_later_submissions_still_work(self):
        next_id = Submission.objects.create(
            submitted_by=self.s2, contest=self.homework, problem=self.p1,
            source_code="x", judge_status_description="In Queue",
        ).pk + 1
        self._import([self._sub(next_id, "s1", self.p1, "考試")], [self._rank(next_id, "s1", 1)])
        later = Submission.objects.create(
            submitted_by=self.s2, contest=self.homework, problem=self.p2,
            source_code="y", judge_status_description="In Queue",
        )
        self.assertGreater(later.pk, next_id - 1)
