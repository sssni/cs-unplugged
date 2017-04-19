from tests.BaseTestWithDB import BaseTestWithDB
from django.urls import reverse


class IndexURLTest(BaseTestWithDB):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_valid_index(self):
        url = reverse('topics:index')
        self.assertEqual(url, '/en/topics/')

        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
