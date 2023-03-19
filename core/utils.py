from idanalyzer import APIError, CoreAPI
from dotenv import load_dotenv
import os

API_REGION = "US"

load_dotenv()


def is_passport_fraud(passport_path):
    try:
        coreapi = CoreAPI(os.getenv("IDANALYZER_API_KEY"), API_REGION)
        coreapi.throw_api_exception(True)
        coreapi.enable_authentication(True, "quick")

        response = coreapi.scan(document_primary=passport_path)

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
