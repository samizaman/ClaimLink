import os
from datetime import datetime

from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from idanalyzer import APIError, CoreAPI

load_dotenv()

API_REGION = "US"
USE_ID_ANALYZER_API = False  # Set to False when you don't want to consume API credits


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
    if name_similarity_score < 80:
        return "name_mismatch", name_similarity_score
    return None, 100


def check_passport_authentication(response):
    if response.get("authentication"):
        authentication_result = response["authentication"]
        if authentication_result["score"] <= 0.5:
            return "not_authentic"
    return None


def check_passport_recognition(response):
    if response.get("authentication") is None:
        return "unrecognized"
    return None


def check_passport_expiry(response):
    # Extract the passport expiry date from the response
    expiry_date_str = response.get("result", {}).get("expiry", "")
    if expiry_date_str:
        # Adjust the date format
        expiry_date_str = expiry_date_str.replace("/", "")
        expiry_date = datetime.strptime(expiry_date_str, "%Y%m%d")

        # Compare the extracted expiry date with the current date
        if expiry_date < datetime.now():
            return "expired_passport"
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

            # Compare the extracted date of birth with the user's date of birth
            if dob != user_dob:
                return "dob_mismatch"
    return None


def check_gender_match(response, user_data):
    # Extract the gender from the response
    gender = response.get("result", {}).get("sex", "").lower()
    if gender:
        # Extract the gender provided by the user
        user_gender = user_data.get("gender", "").lower()

        # Compare the extracted gender with the user's gender
        if gender != user_gender:
            return "gender_mismatch"
    return None


def is_passport_fraud(passport_path, user_data):
    if not USE_ID_ANALYZER_API:
        return {}  # Assume the document is authentic if not using the API

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

        # Print the extracted data
        print("\nIDAnalyzer API Extracted Passport Data:")
        for key, value in extracted_data.items():
            print(f"{key.capitalize()}: {value}")
        print()  # Add an empty line for better readability

        # Call each rule-checking function and aggregate the results
        scores = {
            "name_mismatch": check_name_mismatch(response, user_data),
        }

        # Filter out any None values from the scores dictionary
        scores = {key: value for key, value in scores.items() if value is not None}

        # Read the remaining calls value, update and print the value
        remaining_calls = read_remaining_calls()
        remaining_calls -= 1
        print(f"Remaining calls: {remaining_calls}")
        update_remaining_calls(remaining_calls)

        if response.get("authentication"):
            authentication_result = response["authentication"]
            if authentication_result["score"] > 0.5:
                return scores  # The document uploaded is authentic
            else:
                return scores  # Return the scores for each check
        else:
            return scores  # Authentication not enabled or not available

    except APIError as e:
        details = e.args[0]
        print(
            "API error code: {}, message: {}".format(
                details["code"], details["message"]
            )
        )
        if details["code"] == 9:
            return {"unrecognized": 1}  # Indicate an unrecognized document
        return {}  # If API returns an error, assume the document is not fake

    except Exception as e:
        print(e)
        return {}  # If an exception occurs, assume the document is not fake
