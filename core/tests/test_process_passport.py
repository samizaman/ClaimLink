from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from core.views import process_passport


class ProcessPassportTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def create_test_image(self):
        image = Image.new("RGB", (100, 100))
        img_io = BytesIO()
        image.save(img_io, "JPEG")
        img_io.seek(0)
        return img_io

    def test_valid_passport_image_and_request_with_session_data(self):
        image = self.create_test_image()
        passport = SimpleUploadedFile("test_passport.jpg", image.read())

        request = self.factory.post("/")
        request.session = {
            "personal_details": {"name": "John Doe", "dob": "1990-01-01", "gender": "M"}
        }

        passport_scores = process_passport(passport, request)
        # Based on your analyze_passport() function, the passport_scores should be a dictionary
        self.assertIsInstance(passport_scores, dict)

    def test_invalid_passport_image(self):
        passport = SimpleUploadedFile("invalid_passport.jpg", b"Invalid file content")

        request = self.factory.post("/")
        request.session = {
            "personal_details": {"name": "John Doe", "dob": "1990-01-01", "gender": "M"}
        }

        passport_scores = process_passport(passport, request)
        # Since the passport image is invalid, the analyze_passport() function should return an empty dictionary
        self.assertEqual(passport_scores, {})

    def test_valid_passport_image_and_request_without_session_data(self):
        image = self.create_test_image()
        passport = SimpleUploadedFile("test_passport.jpg", image.read())

        request = self.factory.post("/")
        request.session = {}

        passport_scores = process_passport(passport, request)
        # Since the request does not have session data, the passport_scores should be a dictionary
        self.assertIsInstance(passport_scores, dict)
