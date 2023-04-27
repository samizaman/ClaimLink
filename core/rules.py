from decimal import Decimal

from fuzzywuzzy import fuzz

from core.utils import normalize_score


def compare_names(personal_details_name, passport_name, flight_ticket_name):
    personal_details_name = personal_details_name.lower()
    passport_name = passport_name.lower()
    flight_ticket_name = flight_ticket_name.lower()

    similarity_score_1 = fuzz.ratio(personal_details_name, flight_ticket_name)
    similarity_score_2 = fuzz.ratio(passport_name, flight_ticket_name)

    print(f"Similarity scores: {similarity_score_1}, {similarity_score_2}")

    # Normalize the scores
    min_score = Decimal("0")
    max_score = Decimal("100")
    normalized_similarity_score_1 = normalize_score(
        similarity_score_1, min_score, max_score
    )
    normalized_similarity_score_2 = normalize_score(
        similarity_score_2, min_score, max_score
    )
    print(
        f"Normalized similarity scores: {normalized_similarity_score_1}, {normalized_similarity_score_2}"
    )

    # Set a threshold for the normalized similarity score, e.g., 0.7
    threshold = Decimal("0.7")

    if (
        normalized_similarity_score_1 < threshold
        or normalized_similarity_score_2 < threshold
    ):
        error_type = "flight_ticket_name_mismatch"
        return (
            min(normalized_similarity_score_1, normalized_similarity_score_2),
            error_type,
        )  # Return the lower normalized similarity score and error_type
    return None, None  # Return None if there's no mismatch


def check_extracted_flight_data(extracted_flight_data):
    print("Checking extracted flight data...")  # Debugging print statement
    if all(value is None for value in extracted_flight_data.values()):
        error_type = "incorrect_flight_ticket"
        print("Error detected: ", error_type)  # Debugging print statement
        return error_type
    return None


def process_extracted_flight_data(
    personal_details_name, passport_name, extracted_flight_data
):
    # Check for incorrect or unreadable flight ticket documents
    error_type = check_extracted_flight_data(extracted_flight_data)

    # If an error is detected, return the error_type and a None score
    if error_type:
        return {error_type: None}

    # If no error is detected, proceed with the name comparison
    flight_ticket_first_name = extracted_flight_data.get("first_name", "")
    flight_ticket_last_name = extracted_flight_data.get("last_name", "")
    flight_ticket_name = f"{flight_ticket_first_name} {flight_ticket_last_name}"

    score, error_type = compare_names(
        personal_details_name, passport_name, flight_ticket_name
    )

    # If error_type is not None, return the error type and score
    if error_type:
        return {error_type: score}

    # If everything is fine, return an empty dictionary
    return {}
