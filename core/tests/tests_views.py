from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from core.forms import PersonalDetailsForm


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


class PersonalDetailsViewTests(TestCase):
    def test_personal_details_view_uses_correct_template(self):
        response = self.client.get(reverse("personal_details"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "personal_details.html")

    def test_personal_details_view_form_submission(self):
        response = self.client.post(
            reverse("personal_details"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "name": "John Doe",
                "dob": "1990-01-01",
                "email": "john.doe@example.com",
                "phone_number": "1234567890",
                "gender": "M",
            },
        )

        if response.status_code != 302:
            form = response.context.get("form")
            print("Form errors:", form.errors)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("claim_details"))

    def test_personal_details_view_form_invalid_submission(self):
        response = self.client.post(
            reverse("personal_details"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "dob": "INVALID_DATE",
                "email": "INVALID_EMAIL",
                "phone": "+1 234 567 8900",
            },
        )

        self.assertEqual(response.status_code, 200)
        form = response.context.get("form")
        self.assertIsInstance(form, PersonalDetailsForm)
        self.assertFalse(form.is_valid())


class ClaimDetailsViewTests(TestCase):
    def test_claim_details_view_uses_correct_template(self):
        response = self.client.get(reverse("claim_details"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "claim_details.html")

    def test_claim_details_view_form_submission(self):
        response = self.client.post(
            reverse("claim_details"),
            {
                "date_of_loss": "2022-01-01",
                "country_of_incident": "US",  # <-- Use the correct value here
                "claim_amount": "1000",
                "claim_amount_currency": "USD",
                "description_of_loss": "Lost baggage during travel.",
            },
        )

        if response.status_code != 302:
            form = response.context.get("form")
            print("Form errors:", form.errors)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("coverage_items_selection"))

    def test_claim_details_view_form_submission_with_errors(self):
        response = self.client.post(
            reverse("claim_details"),
            {
                "date_of_loss": "",
                "claim_amount": "1000",
                "description": "Lost baggage during travel.",
            },
        )

        form = response.context.get("form")
        self.assertFalse(form.is_valid())
        self.assertEqual(response.status_code, 200)


class CoverageItemsSelectionViewTests(TestCase):
    def test_coverage_items_selection_view_uses_correct_template(self):
        response = self.client.get(reverse("coverage_items_selection"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "coverage_items_selection.html")

    def test_coverage_items_selection_view_form_submission(self):
        response = self.client.post(
            reverse("coverage_items_selection"),
            {
                "coverage_items": ["Flight Delay or Abandonment", "Baggage Loss"],
            },
        )

        if response.status_code != 302:
            form = response.context.get("form")
            print("Form errors:", form.errors)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("required_documents"))

    def test_coverage_items_selection_view_form_submission_with_errors(self):
        response = self.client.post(
            reverse("coverage_items_selection"),
            {
                "coverage_items": ["Flight Delay or Abandonment", "Invalid Item"],
            },
        )

        form = response.context.get("form")
        self.assertFalse(form.is_valid())
        self.assertEqual(response.status_code, 200)


class RequiredDocumentsViewTests(TestCase):
    def create_temp_image(self, file_name):
        image = Image.new("RGB", (100, 100))
        image_io = BytesIO()
        image.save(image_io, "JPEG")
        image_io.seek(0)
        return SimpleUploadedFile(
            name=file_name, content=image_io.getvalue(), content_type="image/jpeg"
        )

    def test_required_documents_view_uses_correct_template(self):
        response = self.client.get(reverse("required_documents"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "required_documents.html")

    def test_required_documents_view_form_submission(self):
        passport = self.create_temp_image("passport.jpg")
        flight_ticket = self.create_temp_image("flight_ticket.jpg")
        baggage_tag = self.create_temp_image("baggage_tag.jpg")

        response = self.client.post(
            reverse("required_documents"),
            {
                "passport": passport,
                "flight_ticket": flight_ticket,
                "baggage_tag": baggage_tag,
            },
            follow=True,
        )

        if response.status_code != 200:
            form = response.context.get("form")
            print("Form errors:", form.errors)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "claim_summary.html")

    def test_required_documents_view_form_submission_with_errors(self):
        flight_ticket = self.create_temp_image("flight_ticket.jpg")

        response = self.client.post(
            reverse("required_documents"),
            {
                "passport": "",
                "flight_ticket": flight_ticket,
                "baggage_tag": "",
            },
            follow=True,
        )

        form = response.context.get("form")
        self.assertFalse(form.is_valid())
        self.assertEqual(response.status_code, 200)
