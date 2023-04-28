from decimal import Decimal
from django.test import TestCase
from core.views import calculate_total_weighted_sum_of_errors, ERROR_TYPE_WEIGHTS


class CalculateTotalWeightedSumOfErrorsTestCase(TestCase):
    def test_valid_inputs(self):
        passport_scores = {
            "name_mismatch": 30,
            "expired_passport": 20,
            "dob_mismatch": 10,
        }
        flight_ticket_scores = {
            "flight_ticket_passenger_name_mismatch": 15,
            "incorrect_flight_ticket": 25,
        }
        baggage_tag_scores = {
            "incorrect_baggage_tag": 10,
            "airline_name_mismatch": 20,
        }

        total_weighted_sum_of_errors = calculate_total_weighted_sum_of_errors(
            passport_scores, flight_ticket_scores, baggage_tag_scores
        )

        self.assertIsInstance(total_weighted_sum_of_errors[0], Decimal)

    def test_empty_inputs(self):
        passport_scores = {}
        flight_ticket_scores = {}
        baggage_tag_scores = {}

        total_weighted_sum_of_errors = calculate_total_weighted_sum_of_errors(
            passport_scores, flight_ticket_scores, baggage_tag_scores
        )

        self.assertEqual(total_weighted_sum_of_errors[0], Decimal(0))
