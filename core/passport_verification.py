import os
from decimal import Decimal
from datetime import datetime

from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from idanalyzer import APIError, CoreAPI

load_dotenv()

API_REGION = "US"
USE_ID_ANALYZER_API = True  # Set to False when you don't want to consume API credits


def read_remaining_calls():
    with open("core/remaining_calls.txt", "r") as file:
        remaining_calls = int(file.readline().strip())
    return remaining_calls


def update_remaining_calls(remaining_calls):
    with open("core/remaining_calls.txt", "w") as file:
        file.write(str(remaining_calls))


def check_name_mismatch(response, user_data):
    extracted_full_name = response.get("result", {}).get("fullName", "").lower()
    user_name = user_data.get("name", "").lower()

    name_similarity_score = fuzz.ratio(extracted_full_name, user_name)
    print(f"Name similarity score: {name_similarity_score}")

    # Set a threshold for the similarity score, e.g., 80
    threshold = Decimal("80")
    if Decimal(name_similarity_score) < threshold:
        return Decimal(name_similarity_score)  # Return the score if there's a mismatch
    return None  # Return None if there's no mismatch


def check_passport_authentication(response):
    if response.get("authentication"):
        authentication_result = response["authentication"]
        authentication_score = authentication_result["score"]

        # Set a threshold for the authentication score, e.g., 0.5
        threshold = Decimal("0.5")
        if authentication_score <= threshold:
            # Return the authentication score if the passport is not authentic
            return Decimal(authentication_score) * 100
    return None


def check_passport_recognition(response):
    if response.get("authentication") is None:
        # Indicate an unrecognized document with a score of 0
        return Decimal("0")
    return None


def check_passport_expiry(response):
    # Extract the passport expiry date from the response
    expiry_date_str = response.get("result", {}).get("expiry", "")
    if expiry_date_str:
        # Adjust the date format
        expiry_date_str = expiry_date_str.replace("/", "")
        expiry_date = datetime.strptime(expiry_date_str, "%Y%m%d")

        # If the passport is expired, return a similarity score of 0
        if expiry_date < datetime.now():
            return Decimal("0")
        # If the passport is not expired, return a similarity score of 100
        else:
            return Decimal("100")
    return None


def check_dob_match(response, user_data):
    # Extract the date of birth from the response
    dob_str = response.get("result", {}).get("dob", "")
    if dob_str:
        # Convert the date string to a datetime object
        dob_str = dob_str.replace("/", "")
        dob = datetime.strptime(dob_str, "%Y%m%d")

        # Extract the date of birth provided by the user
        user_dob_str = user_data.get("dob", "")
        if user_dob_str:
            # Convert the user date string to a datetime object
            user_dob = datetime.strptime(user_dob_str, "%Y-%m-%d")

            # If the dates are the same, return a similarity score of 100
            if dob == user_dob:
                return Decimal("100")
            # If the dates are different, return a similarity score of 0
            else:
                return Decimal("0")
    return None


def check_gender_match(response, user_data):
    # Extract the gender from the response
    gender = response.get("result", {}).get("sex", "").lower()
    if gender:
        # Extract the gender provided by the user
        user_gender = user_data.get("gender", "").lower()

        # Compare the extracted gender with the user's gender
        if gender == user_gender:
            similarity_score = Decimal("100")
        else:
            similarity_score = Decimal("0")

        # Set a threshold for the similarity score, e.g., 50
        threshold = Decimal("50")

        if similarity_score < threshold:
            return similarity_score
    return None


def analyze_passport(passport_path, user_data):
    """
    Analyze the passport image using the ID Analyzer API and compare the extracted information with the user data.

    :param passport_path: str, path to the uploaded passport image
    :param user_data: dict, user-provided information, including name, date of birth, and gender
    :return: tuple (scores, extracted_data), where:
             - scores: dict, scores for various rule-checking functions indicating any discrepancies or issues
             - extracted_data: dict, data extracted from the passport image, such as name, passport expiry, date of birth, and gender
    """
    if not USE_ID_ANALYZER_API:
        return {}, {}  # Assume the document is authentic if not using the API

    try:
        coreapi = CoreAPI(os.getenv("IDANALYZER_API_KEY"), API_REGION)
        coreapi.throw_api_exception(True)
        coreapi.enable_authentication(True, "quick")

        response = coreapi.scan(document_primary=passport_path)

        # Extract the name, passport expiry, dob, and gender
        extracted_data = {
            "name": response.get("result", {}).get("fullName", ""),
            "passport_expiry": response.get("result", {}).get("expiry", ""),
            "dob": response.get("result", {}).get("dob", ""),
            "gender": response.get("result", {}).get("sex", ""),
        }

        # Call each rule-checking function and aggregate the results
        scores = {
            "name_mismatch": check_name_mismatch(response, user_data),
            "expired_passport": check_passport_expiry(response),
            "dob_mismatch": check_dob_match(response, user_data),
            "gender_mismatch": check_gender_match(response, user_data),
            "not_authentic": check_passport_authentication(response),
            "unrecognized": check_passport_recognition(response),
        }

        # Filter out any None values from the scores dictionary
        scores = {key: value for key, value in scores.items() if value is not None}

        # Read the remaining calls value, update and print the value
        remaining_calls = read_remaining_calls()
        remaining_calls -= 1
        print(f"Remaining calls: {remaining_calls}")
        update_remaining_calls(remaining_calls)

        # If the 'authentication' key exists and the score is less than or equal to 0.5,
        # update the 'not_authentic' score
        if response.get("authentication"):
            authentication_result = response["authentication"]
            if authentication_result["score"] <= 0.5:
                scores["not_authentic"] = 1 - authentication_result["score"]

        # Return both scores and extracted_data
        return scores, extracted_data

    except APIError as e:
        details = e.args[0]
        print(
            "API error code: {}, message: {}".format(
                details["code"], details["message"]
            )
        )
        if details["code"] == 9:
            return {"unrecognized": 1}, {}  # Indicate an unrecognized document
        return {}, {}  # If API returns an error, assume the document is not fake

    except Exception as e:
        print(e)
        return {}, {}  # If an exception occurs, assume the document is not fake
