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
        error_type = "flight_ticket_passenger_name_mismatch"
        return (
            min(normalized_similarity_score_1, normalized_similarity_score_2),
            error_type,
        )  # Return the lower normalized similarity score and error_type
    return None, None  # Return None if there's no mismatch


def check_extracted_flight_data(extracted_flight_data):
    # print("Checking extracted flight data...")  # Debugging print statement
    if all(value is None for value in extracted_flight_data.values()):
        error_type = "incorrect_flight_ticket"
        # print("Error detected: ", error_type)  # Debugging print statement
        return error_type
    return None


def check_extracted_baggage_data(extracted_baggage_data):
    if extracted_baggage_data is None:
        error_type = "incorrect_baggage_tag"
        return error_type
    return None


def check_airline_name(flight_data, baggage_data):
    if not flight_data or not baggage_data:
        return None, None

    flight_airline = flight_data.get("airline_name", "").lower()
    baggage_airline = baggage_data.get("airline_name", "").lower()

    if flight_airline and baggage_airline:
        airline_similarity_score = fuzz.ratio(flight_airline, baggage_airline)
        print(f"Airline similarity score: {airline_similarity_score}")

        # Set a threshold for the similarity score, e.g., 80
        threshold = Decimal("80")
        if Decimal(airline_similarity_score) < threshold:
            error_type = "airline_name_mismatch"
            return (
                Decimal(airline_similarity_score),
                error_type,
            )  # Return the score and error_type if there's a mismatch

    return (
        None,
        None,
    )  # Return None for both score and error_type if there's no mismatch


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


def process_extracted_baggage_data(flight_data, baggage_data):
    # Check for incorrect or unreadable baggage tag documents
    error_type = check_extracted_baggage_data(baggage_data)

    # If an error is detected, return the error_type and a None score
    if error_type:
        return {error_type: None}

    # If no error is detected, proceed with the airline name comparison
    score, error_type = check_airline_name(flight_data, baggage_data)

    # If error_type is not None, return the error type and score
    if error_type:
        return {error_type: score}

    # If everything is fine, return an empty dictionary
    return {}
