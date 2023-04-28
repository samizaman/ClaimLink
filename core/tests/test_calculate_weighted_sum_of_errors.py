from decimal import Decimal
from django.test import TestCase
from core.views import calculate_weighted_sum_of_errors


class CalculateWeightedSumOfErrorsTestCase(TestCase):
    def test_valid_scores_input(self):
        scores = {
            "name_mismatch": 30,
            "expired_passport": 20,
            "dob_mismatch": 10,
        }
        weighted_sum_of_errors, normalized_scores = calculate_weighted_sum_of_errors(
            scores
        )

        self.assertIsInstance(weighted_sum_of_errors, Decimal)
        self.assertIsInstance(normalized_scores, list)
        self.assertEqual(len(normalized_scores), len(scores))

    def test_empty_scores_input(self):
        scores = {}
        weighted_sum_of_errors, normalized_scores = calculate_weighted_sum_of_errors(
            scores
        )

        self.assertEqual(weighted_sum_of_errors, Decimal(0))
        self.assertEqual(normalized_scores, [])

    def test_scores_with_none_values(self):
        scores = {
            "name_mismatch": None,
            "expired_passport": 20,
            "dob_mismatch": 10,
        }
        weighted_sum_of_errors, normalized_scores = calculate_weighted_sum_of_errors(
            scores
        )

        self.assertIsInstance(weighted_sum_of_errors, Decimal)
        self.assertIsInstance(normalized_scores, list)
        self.assertEqual(len(normalized_scores), len(scores))

    def test_scores_with_min_max_values(self):
        scores = {
            "name_mismatch": 0,
            "expired_passport": 100,
            "dob_mismatch": 50,
        }
        weighted_sum_of_errors, normalized_scores = calculate_weighted_sum_of_errors(
            scores
        )

        self.assertIsInstance(weighted_sum_of_errors, Decimal)
        self.assertIsInstance(normalized_scores, list)
        self.assertEqual(len(normalized_scores), len(scores))

    def test_scores_with_negative_values(self):
        scores = {
            "name_mismatch": -10,
            "expired_passport": 20,
            "dob_mismatch": 10,
        }
        weighted_sum_of_errors, normalized_scores = calculate_weighted_sum_of_errors(
            scores
        )

        self.assertIsInstance(weighted_sum_of_errors, Decimal)
        self.assertIsInstance(normalized_scores, list)
        self.assertEqual(len(normalized_scores), len(scores))
