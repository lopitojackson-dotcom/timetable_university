from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardRenderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p', role='super_admin', is_superuser=True)
        self.client = Client()
        self.client.force_login(self.user)

    def test_dashboard(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)

    def test_conflicts(self):
        r = self.client.get('/conflicts/')
        self.assertEqual(r.status_code, 200)

    def test_notifications(self):
        r = self.client.get('/notifications/')
        self.assertEqual(r.status_code, 200)

    def test_history(self):
        r = self.client.get('/conflicts/history/')
        self.assertEqual(r.status_code, 200)