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


def is_passport_fraud(passport_path):
    if not USE_ID_ANALYZER_API:
        return False  # Assume the document is authentic if not using the API
    try:
        coreapi = CoreAPI(os.getenv("IDANALYZER_API_KEY"), API_REGION)
        coreapi.throw_api_exception(True)
        coreapi.enable_authentication(True, "quick")

        response = coreapi.scan(document_primary=passport_path)

        # Read the remaining calls value
        remaining_calls = read_remaining_calls()

        # Decrement the remaining calls and print the value
        remaining_calls -= 1
        print(f"Remaining calls: {remaining_calls}")

        # Update the remaining calls value in the file
        update_remaining_calls(remaining_calls)

        if response.get("authentication"):
            authentication_result = response["authentication"]
            if authentication_result["score"] > 0.5:
                return False  # The document uploaded is authentic
            else:
                return True  # The document uploaded is fake
        else:
            return False  # Authentication not enabled or not available

    except APIError as e:
        details = e.args[0]
        print(
            "API error code: {}, message: {}".format(
                details["code"], details["message"]
            )
        )
        if details["code"] == 9:
            return "unrecognized"
        return False  # If API returns an error, assume the document is not fake

    except Exception as e:
        print(e)
        return False  # If an exception occurs, assume the document is not fake
