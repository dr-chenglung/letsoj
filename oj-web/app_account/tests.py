from django.core.management import call_command
from django.test import Client, TestCase

from app_management.models import MySysOptions

from .models import ExamBindingRejection, ExamIPBinding, SessionWarningUser, User

PC1 = "192.168.0.11"
PC2 = "192.168.0.12"


class ExamIPBindingTests(TestCase):
    def setUp(self):
        call_command("loaddata", "app_management/my-initial-sys-options.json", verbosity=0)
        self.alice = User.objects.create_user("alice", password="pw-alice")
        self.bob = User.objects.create_user("bob", password="pw-bob")
        self.admin = User.objects.create_user("teacher", password="pw-admin", is_staff=True)

    def set_exam_mode(self, on):
        MySysOptions.objects.filter(option_name="exam_ip_binding").update(
            option_value="True" if on else "False"
        )

    def login(self, username, password, ip, client=None):
        client = client or Client()
        resp = client.post(
            "/account/user_login/",
            {"username": username, "password": password},
            HTTP_X_REAL_IP=ip,
        )
        return client, resp

    def assert_logged_in(self, client):
        self.assertIn("_auth_user_id", client.session)

    def assert_not_logged_in(self, client):
        self.assertNotIn("_auth_user_id", client.session)

    def test_disabled_mode_does_not_bind(self):
        c1, _ = self.login("alice", "pw-alice", PC1)
        c2, _ = self.login("alice", "pw-alice", PC2)
        self.assert_logged_in(c1)
        self.assert_logged_in(c2)
        self.assertEqual(ExamIPBinding.objects.count(), 0)

    def test_first_login_binds_ip(self):
        self.set_exam_mode(True)
        c, _ = self.login("alice", "pw-alice", PC1)
        self.assert_logged_in(c)
        self.assertEqual(ExamIPBinding.objects.get(user=self.alice).ip, PC1)

    def test_same_account_other_pc_rejected(self):
        self.set_exam_mode(True)
        self.login("alice", "pw-alice", PC1)
        c, _ = self.login("alice", "pw-alice", PC2)
        self.assert_not_logged_in(c)
        self.assertEqual(ExamBindingRejection.objects.filter(user=self.alice).count(), 1)

    def test_same_account_same_pc_relogin_ok(self):
        self.set_exam_mode(True)
        self.login("alice", "pw-alice", PC1)
        c, _ = self.login("alice", "pw-alice", PC1)
        self.assert_logged_in(c)

    def test_second_account_same_pc_rejected(self):
        # 同一台電腦換瀏覽器登入別的帳號
        self.set_exam_mode(True)
        self.login("alice", "pw-alice", PC1)
        c, _ = self.login("bob", "pw-bob", PC1)
        self.assert_not_logged_in(c)
        self.assertFalse(ExamIPBinding.objects.filter(user=self.bob).exists())

    def test_staff_exempt(self):
        self.set_exam_mode(True)
        self.login("alice", "pw-alice", PC1)
        c, _ = self.login("teacher", "pw-admin", PC1)
        self.assert_logged_in(c)
        self.assertFalse(ExamIPBinding.objects.filter(user=self.admin).exists())

    def test_internal_ip_not_bound(self):
        # 伺服器只看到 Docker 閘道 IP 時不能綁定，否則第一個人會綁走全班的 IP
        self.set_exam_mode(True)
        c, _ = self.login("alice", "pw-alice", "172.18.0.1")
        self.assert_not_logged_in(c)
        self.assertEqual(ExamIPBinding.objects.count(), 0)

    def post_sys_options(self, admin_client, exam_on):
        return admin_client.post("/manage/sys_options/", {
            "forbid_login_ip": "False",
            "forbid_login_session": "False",
            "allowed_ip_ranges": "",
            "forbid_password_change": "False",
            "allow_user_register": "False",
            "hide_submitted_code": "False",
            "exam_ip_binding": "True" if exam_on else "False",
        })

    def test_turning_on_logs_out_students_but_not_staff(self):
        # 開關打開前就登入的人(例如在別台電腦用別人帳號)必須被登出
        c_student, _ = self.login("alice", "pw-alice", PC2)
        admin_client, _ = self.login("teacher", "pw-admin", PC1)
        self.post_sys_options(admin_client, exam_on=True)
        self.assert_not_logged_in(c_student)
        self.assert_logged_in(admin_client)

    def test_saving_settings_while_already_on_keeps_sessions(self):
        # 開關本來就開著時，修改其他設定不應該登出考生
        self.set_exam_mode(True)
        c_student, _ = self.login("alice", "pw-alice", PC2)
        admin_client, _ = self.login("teacher", "pw-admin", PC1)
        self.post_sys_options(admin_client, exam_on=True)
        self.assert_logged_in(c_student)

    def test_turning_off_keeps_sessions(self):
        self.set_exam_mode(True)
        c_student, _ = self.login("alice", "pw-alice", PC2)
        admin_client, _ = self.login("teacher", "pw-admin", PC1)
        self.post_sys_options(admin_client, exam_on=False)
        self.assert_logged_in(c_student)

    def test_reset_binding_logs_out_only_that_student(self):
        self.set_exam_mode(True)
        c_alice, _ = self.login("alice", "pw-alice", PC1)
        c_bob, _ = self.login("bob", "pw-bob", PC2)
        admin_client, _ = self.login("teacher", "pw-admin", "192.168.0.99")
        resp = admin_client.post("/manage/reset_exam_ip_binding/", {"username": "alice"})
        self.assertTrue(resp.json()["success"])
        self.assert_not_logged_in(c_alice)
        self.assert_logged_in(c_bob)
        self.assert_logged_in(admin_client)
        # alice 到新電腦登入，綁定新的電腦
        c, _ = self.login("alice", "pw-alice", "192.168.0.13")
        self.assert_logged_in(c)
        self.assertEqual(ExamIPBinding.objects.get(user=self.alice).ip, "192.168.0.13")

    def test_clear_all_bindings_logs_out_students(self):
        # 開關一直開著時清除綁定，舊綁定的登入狀態不能留著
        self.set_exam_mode(True)
        c_alice, _ = self.login("alice", "pw-alice", PC1)
        admin_client, _ = self.login("teacher", "pw-admin", PC2)
        admin_client.post("/manage/clear_exam_ip_bindings/")
        self.assertEqual(ExamIPBinding.objects.count(), 0)
        self.assert_not_logged_in(c_alice)
        self.assert_logged_in(admin_client)

    def test_relogin_after_clear_is_not_flagged_as_multiple_login(self):
        # 單一登入開著時，被清掉登入狀態後重新登入，不應被誤記為多次登入
        MySysOptions.objects.filter(option_name="forbid_login_session").update(option_value="True")
        self.login("alice", "pw-alice", PC1)
        admin_client, _ = self.login("teacher", "pw-admin", PC2)
        self.post_sys_options(admin_client, exam_on=True)
        self.login("alice", "pw-alice", PC1)
        self.assertFalse(SessionWarningUser.objects.filter(user=self.alice).exists())

    def test_binding_views_require_staff(self):
        c, _ = self.login("alice", "pw-alice", PC1)
        resp = c.post("/manage/clear_exam_ip_bindings/")
        self.assertEqual(resp.status_code, 302)  # 導向管理者登入
        resp = c.get("/manage/get_exam_ip_bindings/")
        self.assertEqual(resp.status_code, 302)

    def test_sys_options_api_creates_missing_option(self):
        # 舊資料庫沒有 exam_ip_binding 這一列
        MySysOptions.objects.filter(option_name="exam_ip_binding").delete()
        admin_client, _ = self.login("teacher", "pw-admin", PC1)
        resp = admin_client.post("/manage/sys_options/", {
            "forbid_login_ip": "False",
            "forbid_login_session": "False",
            "allowed_ip_ranges": "",
            "forbid_password_change": "False",
            "allow_user_register": "False",
            "hide_submitted_code": "False",
            "exam_ip_binding": "True",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            MySysOptions.objects.get(option_name="exam_ip_binding").option_value, "True"
        )
