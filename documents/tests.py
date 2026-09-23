from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Document, ShareLink


class UploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='uploaduser', password='TestPass123!')
        self.client.login(username='uploaduser', password='TestPass123!')

    def test_upload_valid_pdf(self):
        fake_pdf = SimpleUploadedFile(
            "test_certificate.pdf",
            b"%PDF-1.4 fake pdf content",
            content_type="application/pdf"
        )
        response = self.client.post(reverse('upload'), {
            'title': 'My Certificate',
            'file': fake_pdf,
        })
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.owner, self.user)
        self.assertTrue(doc.encrypted_file_key)  # confirms per-file key was generated

    def test_upload_rejects_disallowed_file_type(self):
        fake_exe = SimpleUploadedFile(
            "virus.exe",
            b"fake executable content",
            content_type="application/octet-stream"
        )
        response = self.client.post(reverse('upload'), {
            'title': 'Suspicious File',
            'file': fake_exe,
        })
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 302)  # redirected to login


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='dashuser', password='TestPass123!')
        self.other_user = User.objects.create_user(username='otheruser', password='TestPass123!')
        self.client.login(username='dashuser', password='TestPass123!')

    def test_dashboard_only_shows_own_documents(self):
        Document.objects.create(owner=self.user, title='My Doc', category='cv')
        Document.objects.create(owner=self.other_user, title='Not Mine', category='cv')

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'My Doc')
        self.assertNotContains(response, 'Not Mine')

    def test_dashboard_pagination(self):
        for i in range(10):
            Document.objects.create(owner=self.user, title=f'Doc {i}', category='cv')

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(len(response.context['documents']), 8)  # first page shows 8


class ShareLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='shareuser', password='TestPass123!')
        self.client.login(username='shareuser', password='TestPass123!')
        self.document = Document.objects.create(owner=self.user, title='Shared Doc', category='cv')

    def test_create_share_link(self):
        response = self.client.get(reverse('create_share_link', args=[self.document.id]))
        self.assertEqual(ShareLink.objects.count(), 1)
        self.assertEqual(response.status_code, 200)

    def test_cannot_share_another_users_document(self):
        other_user = User.objects.create_user(username='intruder', password='TestPass123!')
        self.client.login(username='intruder', password='TestPass123!')

        response = self.client.get(reverse('create_share_link', args=[self.document.id]))
        self.assertEqual(response.status_code, 404)  # can't access someone else's document