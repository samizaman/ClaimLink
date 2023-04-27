from decimal import Decimal

from fuzzywuzzy import fuzz

from core.utils import MAX_SCORE, MIN_SCORE, normalize_score


def compare_personal_details_and_flight_ticket_name(
    personal_details_name, flight_ticket_name
):
    personal_details_name = personal_details_name.lower()
    flight_ticket_name = flight_ticket_name.lower()

    similarity_score = fuzz.ratio(personal_details_name, flight_ticket_name)
    print(f"Personal details vs flight ticket similarity score: {similarity_score}")

    normalized_similarity_score = normalize_score(
        similarity_score, MIN_SCORE, MAX_SCORE
    )
    print(f"Normalized similarity score: {normalized_similarity_score}")

    threshold = Decimal("0.7")

    if normalized_similarity_score < threshold:
        error_type = "flight_ticket_personal_details_name_mismatch"
        return normalized_similarity_score, error_type

    return None, None


def compare_passport_and_flight_ticket_name(passport_name, flight_ticket_name):
    passport_name = passport_name.lower()
    flight_ticket_name = flight_ticket_name.lower()

    similarity_score = fuzz.ratio(passport_name, flight_ticket_name)
    print(f"Passport vs flight ticket similarity score: {similarity_score}")

    normalized_similarity_score = normalize_score(
        similarity_score, MIN_SCORE, MAX_SCORE
    )
    print(f"Normalized similarity score: {normalized_similarity_score}")

    threshold = Decimal("0.7")

    if normalized_similarity_score < threshold:
        error_type = "flight_ticket_passport_name_mismatch"
        return normalized_similarity_score, error_type

    return None, None


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

    score_1, error_type_1 = compare_personal_details_and_flight_ticket_name(
        personal_details_name, flight_ticket_name
    )
    score_2, error_type_2 = compare_passport_and_flight_ticket_name(
        passport_name, flight_ticket_name
    )

    # If any of the error_types is not None, return the corresponding error type and score
    if error_type_1:
        return {error_type_1: score_1}
    if error_type_2:
        return {error_type_2: score_2}

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
