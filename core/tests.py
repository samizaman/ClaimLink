from django.test import Client, TestCase
from django.urls import reverse


class HomeViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view_success(self):
        # Issue a GET request to the home page
        response = self.client.get(reverse("home"))

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check if the correct template is used to render the response
        self.assertTemplateUsed(response, "home.html")
