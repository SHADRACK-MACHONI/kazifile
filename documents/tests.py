from django.test import TestCase
from documents.utils import get_fernet_key


class ProjectRuntimeTests(TestCase):
    def test_root_page_loads_on_localhost(self):
        response = self.client.get('/', HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)

    def test_fernet_key_has_a_valid_default(self):
        key = get_fernet_key()
        self.assertIsNotNone(key)
