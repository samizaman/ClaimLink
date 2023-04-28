from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from PIL import Image

from core.views import process_flight_ticket


class ProcessFlightTicketTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def create_test_image(self):
        image = Image.new("RGB", (100, 100))
        img_io = BytesIO()
        image.save(img_io, "JPEG")
        img_io.seek(0)
        return img_io

    def test_valid_flight_ticket_image_and_request_with_session_data(self):
        image = self.create_test_image()
        flight_ticket = SimpleUploadedFile("test_flight_ticket.jpg", image.read())

        request = self.factory.post("/")
        request.session = {
            "personal_details": {
                "name": "John Doe",
                "dob": "1990-01-01",
                "gender": "M",
            },
            "passport_data": {"name": "JOHN DOE", "dob": "1990-01-01", "gender": "M"},
        }

        extracted_flight_data, flight_ticket_scores = process_flight_ticket(
            flight_ticket, request
        )
        self.assertIsInstance(extracted_flight_data, dict)
        self.assertIsInstance(flight_ticket_scores, dict)

    def test_invalid_flight_ticket_image(self):
        flight_ticket = SimpleUploadedFile(
            "invalid_flight_ticket.jpg", b"Invalid file content"
        )

        request = self.factory.post("/")
        request.session = {
            "personal_details": {
                "name": "John Doe",
                "dob": "1990-01-01",
                "gender": "M",
            },
            "passport_data": {"name": "JOHN DOE", "dob": "1990-01-01", "gender": "M"},
        }

        extracted_flight_data, flight_ticket_scores = process_flight_ticket(
            flight_ticket, request
        )
        self.assertIsInstance(extracted_flight_data, dict)
        self.assertDictEqual(flight_ticket_scores, {"incorrect_flight_ticket": Decimal("100")})

    def test_valid_flight_ticket_image_and_request_without_session_data(self):
        image = self.create_test_image()
        flight_ticket = SimpleUploadedFile("test_flight_ticket.jpg", image.read())

        request = self.factory.post("/")
        request.session = {}

        extracted_flight_data, flight_ticket_scores = process_flight_ticket(
            flight_ticket, request
        )
        self.assertIsInstance(extracted_flight_data, dict)
        self.assertIsNone(flight_ticket_scores)
