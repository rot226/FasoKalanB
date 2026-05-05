from django.test import TestCase


class HomeViewTests(TestCase):
    def test_get_home_returns_200_and_expected_content(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bienvenue sur FasoKalanB')
