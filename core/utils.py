import os

from dotenv import load_dotenv
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

    if extracted_full_name != user_name:
        return "name_mismatch"
    return None


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


def is_passport_fraud(passport_path, user_data):
    if not USE_ID_ANALYZER_API:
        return []  # Assume the document is authentic if not using the API

    try:
        coreapi = CoreAPI(os.getenv("IDANALYZER_API_KEY"), API_REGION)
        coreapi.throw_api_exception(True)
        coreapi.enable_authentication(True, "quick")

        response = coreapi.scan(document_primary=passport_path)

        # Call each rule-checking function and aggregate the results
        violations = []
        violations.append(check_name_mismatch(response, user_data))
        violations.append(check_passport_authentication(response))
        violations.append(check_passport_recognition(response))

        # Filter out any None values from the violations list
        violations = [violation for violation in violations if violation]

        # Read the remaining calls value, update and print the value
        remaining_calls = read_remaining_calls()
        remaining_calls -= 1
        print(f"Remaining calls: {remaining_calls}")
        update_remaining_calls(remaining_calls)

        if response.get("authentication"):
            authentication_result = response["authentication"]
            if authentication_result["score"] > 0.5:
                return violations  # The document uploaded is authentic
            else:
                return violations  # Return the violated rules
        else:
            return violations  # Authentication not enabled or not available

    except APIError as e:
        details = e.args[0]
        print(
            "API error code: {}, message: {}".format(
                details["code"], details["message"]
            )
        )
        if details["code"] == 9:
            return ["unrecognized"]
        return []  # If API returns an error, assume the document is not fake

    except Exception as e:
        print(e)
        return []  # If an exception occurs, assume the document is not fake
