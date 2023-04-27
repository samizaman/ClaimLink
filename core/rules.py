from decimal import Decimal

from fuzzywuzzy import fuzz

from core.utils import MAX_SCORE, MIN_SCORE, normalize_score


def compare_personal_details_and_flight_ticket_name(
    personal_details_name, flight_ticket_name
):
    personal_details_name = personal_details_name.lower()
    flight_ticket_name = flight_ticket_name.lower()

    similarity_score = fuzz.ratio(personal_details_name, flight_ticket_name)

    normalized_similarity_score = normalize_score(
        similarity_score, MIN_SCORE, MAX_SCORE
    )

    threshold = Decimal("0.7")

    if normalized_similarity_score < threshold:
        error_type = "flight_ticket_personal_details_name_mismatch"
        return normalized_similarity_score, error_type

    return None, None


def compare_passport_and_flight_ticket_name(passport_name, flight_ticket_name):
    passport_name = passport_name.lower()
    flight_ticket_name = flight_ticket_name.lower()

    similarity_score = fuzz.ratio(passport_name, flight_ticket_name)

    normalized_similarity_score = normalize_score(
        similarity_score, MIN_SCORE, MAX_SCORE
    )

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


def check_booking_reference(flight_data, baggage_data):
    if not flight_data or not baggage_data:
        return None, None

    flight_booking_reference = flight_data.get("booking_reference_number", "").lower()
    baggage_booking_reference = baggage_data.get("booking_reference_number", "").lower()

    if flight_booking_reference and baggage_booking_reference:
        booking_reference_similarity_score = fuzz.ratio(
            flight_booking_reference, baggage_booking_reference
        )
        print(
            f"Booking reference similarity score: {booking_reference_similarity_score}"
        )

        # Set a threshold for the similarity score, e.g., 80
        threshold = Decimal("80")
        if Decimal(booking_reference_similarity_score) < threshold:
            error_type = "booking_reference_mismatch"
            return (
                Decimal(booking_reference_similarity_score),
                error_type,
            )  # Return the score and error_type if there's a mismatch

    return (
        None,
        None,
    )  # Return None for both score and error_type if there's no mismatch


def check_passenger_name(flight_data, baggage_data):
    if not flight_data or not baggage_data:
        return None, None

    flight_ticket_first_name = flight_data.get("first_name", "").lower()
    flight_ticket_last_name = flight_data.get("last_name", "").lower()
    flight_ticket_name = f"{flight_ticket_first_name} {flight_ticket_last_name}"

    baggage_passenger_name = baggage_data.get("passenger_name", "").lower()

    if flight_ticket_name and baggage_passenger_name:
        passenger_name_similarity_score = fuzz.ratio(
            flight_ticket_name, baggage_passenger_name
        )
        print(f"Passenger name similarity score: {passenger_name_similarity_score}")

        # Set a threshold for the similarity score, e.g., 80
        threshold = Decimal("80")
        if Decimal(passenger_name_similarity_score) < threshold:
            error_type = "passenger_name_mismatch"
            return (
                Decimal(passenger_name_similarity_score),
                error_type,
            )  # Return the score and error_type if there's a mismatch

    return (
        None,
        None,
    )  # Return None for both score and error_type if there's no mismatch


def process_extracted_flight_data(personal_details_name, passport_name, flight_data):
    # Check for incorrect or unreadable flight ticket documents
    flight_error = check_extracted_flight_data(flight_data)

    # If an error is detected, return the error_type and a None score
    if flight_error:
        return {flight_error: None}

    errors = {}

    # Extract flight ticket name
    first_name = flight_data.get("first_name", "")
    last_name = flight_data.get("last_name", "")
    ticket_name = f"{first_name} {last_name}"

    # Define a list of comparison functions with their corresponding arguments
    comparison_functions = [
        (compare_personal_details_and_flight_ticket_name, personal_details_name),
        (compare_passport_and_flight_ticket_name, passport_name),
    ]

    for compare_func, name in comparison_functions:
        score, error_type = compare_func(name, ticket_name)
        if error_type:
            errors[error_type] = score

    # Return the errors dictionary
    return errors


def process_extracted_baggage_data(flight_data, baggage_data):
    # Check for incorrect or unreadable baggage tag documents
    baggage_error = check_extracted_baggage_data(baggage_data)

    # If an error is detected, return the error_type and a None score
    if baggage_error:
        return {baggage_error: None}

    errors = {}

    # Define a list of comparison functions
    comparison_functions = [
        check_airline_name,
        check_booking_reference,
        check_passenger_name,
    ]

    for compare_func in comparison_functions:
        score, error_type = compare_func(flight_data, baggage_data)
        if error_type:
            errors[error_type] = score

    # Return the errors dictionary
    return errors
