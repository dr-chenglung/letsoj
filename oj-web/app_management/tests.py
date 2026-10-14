from django.test import Client, TestCase

from app_account.models import LoginHistory, User

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

