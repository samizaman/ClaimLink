from fuzzywuzzy import fuzz
from decimal import Decimal


def compare_names(personal_details_name, passport_name, flight_ticket_name):
    personal_details_name = personal_details_name.lower()
    passport_name = passport_name.lower()
    flight_ticket_name = flight_ticket_name.lower()

    similarity_score_1 = fuzz.ratio(personal_details_name, flight_ticket_name)
    similarity_score_2 = fuzz.ratio(passport_name, flight_ticket_name)

    print(f"Similarity scores: {similarity_score_1}, {similarity_score_2}")

    # Set a threshold for the similarity score, e.g., 70
    threshold = Decimal("70")

    if (
        Decimal(similarity_score_1) < threshold
        or Decimal(similarity_score_2) < threshold
    ):
        error_type = "flight_ticket_name_mismatch"
        return (
            min(similarity_score_1, similarity_score_2),
            error_type,
        )  # Return the lower similarity score and error_type
    return None, None  # Return None if there's no mismatch
