from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache


class SignupTests(TestCase):
    def test_signup_creates_user(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.first().username, 'testuser')

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password1': 'StrongPass123!',
            'password2': 'DifferentPass456!',
        })
        self.assertEqual(User.objects.count(), 0)


class LoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='loginuser', password='TestPass123!')

    def test_login_with_correct_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_with_wrong_password_fails(self):
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct")

    def test_lockout_after_repeated_failures(self):
        for _ in range(5):
            self.client.post(reverse('login'), {
                'username': 'loginuser',
                'password': 'WrongPassword!',
            })
        response = self.client.get(reverse('login'))
        self.assertContains(response, "Too many failed login attempts")