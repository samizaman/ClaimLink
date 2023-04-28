from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase

from core.views import process_baggage_tag


class ProcessBaggageTagTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_process_baggage_tag_valid(self):
        baggage_tag = SimpleUploadedFile("baggage_tag.jpg", b"baggage_tag_data")

        request = self.factory.post("/")
        request.session = {"flight_data": {"dummy": "flight_data"}}

        with patch("core.views.default_storage") as mock_storage, \
             patch("core.views.process_baggage_tag_image") as mock_process_baggage_tag_image, \
             patch("core.views.os.remove") as mock_os_remove, \
             patch("core.views.process_extracted_baggage_data") as mock_process_extracted_baggage_data:

            mock_storage.save.return_value = "temp/baggage_tag.jpg"
            mock_storage.path.return_value = "/path/to/temp/baggage_tag.jpg"
            mock_process_baggage_tag_image.return_value = {"dummy": "baggage_data"}
            mock_process_extracted_baggage_data.return_value = {"dummy": "baggage_scores"}

            extracted_baggage_data, baggage_tag_scores = process_baggage_tag(baggage_tag, request)

            self.assertEqual(extracted_baggage_data, {"dummy": "baggage_data"})
            self.assertEqual(baggage_tag_scores, {"dummy": "baggage_scores"})

    def test_process_baggage_tag_no_flight_data(self):
        baggage_tag = SimpleUploadedFile("baggage_tag.jpg", b"baggage_tag_data")

        request = self.factory.post("/")
        request.session = {}

        with patch("core.views.default_storage") as mock_storage, \
             patch("core.views.process_baggage_tag_image") as mock_process_baggage_tag_image, \
             patch("core.views.os.remove") as mock_os_remove:

            mock_storage.save.return_value = "temp/baggage_tag.jpg"
            mock_storage.path.return_value = "/path/to/temp/baggage_tag.jpg"
            mock_process_baggage_tag_image.return_value = {"dummy": "baggage_data"}

            extracted_baggage_data, baggage_tag_scores = process_baggage_tag(baggage_tag, request)

            self.assertEqual(extracted_baggage_data, {"dummy": "baggage_data"})
            self.assertIsNone(baggage_tag_scores)
