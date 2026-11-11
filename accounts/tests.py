from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(TestCase):
    def test_create_user(self):
        u = User.objects.create_user(username='u1', password='pass123', role='student')
        self.assertEqual(u.role, 'student')
        self.assertTrue(u.check_password('pass123'))

    def test_login(self):
        User.objects.create_user(username='u2', password='pass123')
        resp = self.client.post('/accounts/login/', {'username':'u2','password':'pass123'})
        self.assertEqual(resp.status_code, 302)
