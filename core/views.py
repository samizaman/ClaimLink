import json
import os
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.shortcuts import redirect, render
from dotenv import load_dotenv
from web3 import Web3

from core.models import (
    Claim,
    CoverageItem,
    Customer,
)
from core.passport_verification import analyze_passport
from .baggage_tag_extractor.baggage_tag import process_baggage_tag_image
from .blockchain import add_claim_to_blockchain, prepare_claim_transaction
from .flight_ticket_extractor.flight_ticket_info_extractor import extract_ticket_info
from .forms import (
    ClaimDetailsForm,
    CoverageItemsSelectionForm,
    PersonalDetailsForm,
    RequiredDocumentsForm,
)
from .rules import process_extracted_baggage_data, process_extracted_flight_data
from .utils import normalize_score

load_dotenv()

goerli_url = f"https://goerli.infura.io/v3/{os.getenv('INFURA_PROJECT_ID')}"
w3 = Web3(Web3.HTTPProvider(goerli_url))
SEVERITY_THRESHOLDS = {
    "Low": Decimal("0.2"),
    "Medium": Decimal("0.5"),
    "High": Decimal("1.0"),
}
ERROR_TYPE_WEIGHTS = {
    "name_mismatch": Decimal("0.25"),
    "expired_passport": Decimal("0.2"),
    "dob_mismatch": Decimal("0.2"),
    "gender_mismatch": Decimal("0.2"),
    "unrecognized": Decimal("0.1"),
    "not_authentic": Decimal("0.05"),
    "flight_ticket_passenger_name_mismatch": Decimal("0.1"),
    "incorrect_flight_ticket": Decimal("0.1"),
    "incorrect_baggage_tag": Decimal("0.1"),
    "airline_name_mismatch": Decimal("0.1"),
    "flight_ticket_personal_details_name_mismatch": Decimal("0.1"),
    "flight_ticket_passport_name_mismatch": Decimal("0.1"),
    "booking_reference_mismatch": Decimal("0.1"),
    "passenger_name_mismatch": Decimal("0.1"),
    "invalid_emirates_barcode": Decimal("0.1"),
}


def home(request):
    return render(request, "home.html")


def personal_details(request):
    if request.method == "POST":
        form = PersonalDetailsForm(request.POST)
        if form.is_valid():
            personal_details = form.cleaned_data
            # Convert the date object to a string
            personal_details["dob"] = personal_details["dob"].strftime("%Y-%m-%d")
            request.session["personal_details"] = personal_details
            print(f"Personal details: {request.session['personal_details']}")
            return redirect("claim_details")
    else:
        form = PersonalDetailsForm()

    return render(request, "personal_details.html", {"form": form})


def claim_details(request):
    if request.method == "POST":
        form = ClaimDetailsForm(request.POST)
        if form.is_valid():
            claim_details = form.cleaned_data
            # Convert the date object to a string
            claim_details["date_of_loss"] = claim_details["date_of_loss"].strftime(
                "%Y-%m-%d"
            )
            # Convert Decimal object to string
            claim_details["claim_amount"] = str(claim_details["claim_amount"])
            request.session["claim_details"] = claim_details
            print(f"Claim details: {request.session['claim_details']}")
            return redirect("coverage_items_selection")

    else:
        form = ClaimDetailsForm()

    return render(
        request,
        "claim_details.html",
        {"form": form},
    )


def coverage_items_selection(request):
    if request.method == "POST":
        form = CoverageItemsSelectionForm(request.POST)
        if form.is_valid():
            coverage_items = form.cleaned_data["coverage_items"]
            request.session["coverage_items"] = coverage_items
            return redirect("required_documents")

    # Load previously selected coverage items from session
    selected_coverage_items = request.session.get("coverage_items", [])
    print(f"Selected coverage items: {selected_coverage_items}")

    form = CoverageItemsSelectionForm(
        initial={"coverage_items": selected_coverage_items}
    )

    return render(
        request,
        "coverage_items_selection.html",
        {"form": form, "selected_coverage_items": selected_coverage_items},
    )


def calculate_weighted_sum_of_errors(scores):
    """
    Calculates the weighted sum of errors and normalized scores for a given dictionary of scores.

    Args:
        scores (dict): A dictionary containing error types as keys and their respective scores as values.

    Returns:
        tuple: A tuple containing the weighted sum of errors (Decimal) and a list of normalized scores.
    """
    # Define the minimum and maximum possible scores for normalization
    min_score = Decimal("0")
    max_score = Decimal("100")

    # Normalize the scores
    normalized_scores = [
        normalize_score(score, min_score, max_score) if score is not None else None
        for score in scores.values()
    ]

    # Calculate the weighted sum of errors
    weighted_sum_of_errors = sum(
        (Decimal("1") - score) * ERROR_TYPE_WEIGHTS[error_type]
        if score is not None
        else ERROR_TYPE_WEIGHTS[error_type]
        for score, error_type in zip(normalized_scores, scores.keys())
    )

    return weighted_sum_of_errors, normalized_scores


def calculate_total_weighted_sum_of_errors(
    passport_scores, flight_ticket_scores, baggage_tag_scores
):
    """
    Calculates the total weighted sum of errors and error types for given dictionaries of passport, flight ticket, and baggage tag scores.

    Args:
        passport_scores (dict): A dictionary containing passport error types as keys and their respective scores as values.
        flight_ticket_scores (dict): A dictionary containing flight ticket error types as keys and their respective scores as values.
        baggage_tag_scores (dict): A dictionary containing baggage tag error types as keys and their respective scores as values.

    Returns:
        tuple: A tuple containing the total weighted sum of errors (Decimal) and a list of error types where the normalized score is below 0.5.
    """
    # Combine the passport_scores, flight_ticket_scores, and baggage_tag_scores dictionaries
    all_scores = {
        **(passport_scores or {}),
        **(flight_ticket_scores or {}),
        **(baggage_tag_scores or {}),
    }

    weighted_sum_of_errors, normalized_scores = calculate_weighted_sum_of_errors(
        all_scores
    )

    # Get the error types where the normalized score is below 0.5
    error_types = [
        key
        for key, score in zip(all_scores.keys(), normalized_scores)
        if score is None or (score is not None and score < 0.5)
    ]

    return weighted_sum_of_errors, error_types


def process_passport(passport, request):
    passport_path = default_storage.save(f"passport_photos/{passport.name}", passport)
    passport_actual_path = default_storage.path(passport_path)

    customer_details = request.session.get("personal_details", None)
    user_data = (
        {
            "name": customer_details.get("name", ""),
            "dob": customer_details.get("dob", ""),
            "gender": customer_details.get("gender", ""),
        }
        if customer_details
        else {"name": "", "dob": "", "gender": ""}
    )

    passport_scores, passport_data = analyze_passport(passport_actual_path, user_data)
    print(f"Passport scores: {passport_scores}")
    print(f"Passport data: {passport_data}")

    request.session["passport_data"] = passport_data

    return passport_scores


def process_flight_ticket(flight_ticket, request):
    flight_ticket_path = default_storage.save(
        f"temp/{flight_ticket.name}", flight_ticket
    )
    flight_ticket_temp_path = default_storage.path(flight_ticket_path)

    extracted_flight_data = extract_ticket_info(flight_ticket_temp_path) or {}
    print(f"Extracted flight data: {extracted_flight_data}")
    os.remove(flight_ticket_temp_path)

    # Store the extracted_flight_data in the session
    request.session["flight_data"] = extracted_flight_data

    # Retrieve personal details and passport data from the session
    personal_details = request.session.get("personal_details", None)
    passport_data = request.session.get("passport_data", None)

    if personal_details and passport_data:
        personal_details_name = personal_details.get("name", "")
        passport_name = passport_data.get("name", "")

        flight_ticket_scores = process_extracted_flight_data(
            personal_details_name, passport_name, extracted_flight_data
        )
        print(
            "Flight ticket scores: ", flight_ticket_scores
        )  # Debugging print statement
        return extracted_flight_data, flight_ticket_scores
    return extracted_flight_data, None


def process_baggage_tag(baggage_tag, request):
    baggage_tag_path = default_storage.save(f"temp/{baggage_tag.name}", baggage_tag)
    baggage_tag_temp_path = default_storage.path(baggage_tag_path)

    extracted_baggage_data = process_baggage_tag_image(baggage_tag_temp_path)
    print(f"Extracted baggage data: {extracted_baggage_data}")
    os.remove(baggage_tag_temp_path)

    # Retrieve flight_data from the session
    flight_data = request.session.get("flight_data", None)

    if flight_data:
        baggage_tag_scores = process_extracted_baggage_data(
            flight_data, extracted_baggage_data
        )
        print("baggage_tag_scores: ", baggage_tag_scores)  # Debugging print statement

        # Return the extracted baggage data along with the results
        return extracted_baggage_data, baggage_tag_scores

    return extracted_baggage_data, None


def required_documents(request):
    selected_coverage_items = request.session.get("coverage_items", [])

    if request.method == "POST":
        form = RequiredDocumentsForm(request.POST, request.FILES)
        if form.is_valid():
            flight_ticket = form.cleaned_data["flight_ticket"]
            baggage_tag = form.cleaned_data.get("baggage_tag", None)
            passport = form.cleaned_data["passport"]

            if flight_ticket:
                extracted_flight_data, flight_ticket_scores = process_flight_ticket(
                    flight_ticket, request
                )
            else:
                extracted_flight_data, flight_ticket_scores = None, None

            if baggage_tag:
                extracted_baggage_data, baggage_tag_scores = process_baggage_tag(
                    baggage_tag, request
                )
            else:
                extracted_baggage_data, baggage_tag_scores = None, None

            if passport:
                passport_scores = process_passport(passport, request)
            else:
                passport_scores = None

            (
                weighted_sum_of_errors,
                error_types,
            ) = calculate_total_weighted_sum_of_errors(
                passport_scores, flight_ticket_scores, baggage_tag_scores
            )
            print(
                f"Weighted sum of errors in Required Documents: {weighted_sum_of_errors}"
            )
            print(f"Error Types in Required Documents: {error_types}")
            request.session["weighted_sum_of_errors"] = str(weighted_sum_of_errors)
            request.session["error_types"] = error_types

            return redirect("claim_summary")

        else:
            error_message = "Please make sure all required fields are filled correctly."
    else:
        form = RequiredDocumentsForm()
        error_message = None

    return render(
        request,
        "required_documents.html",
        {
            "form": form,
            "selected_coverage_items": selected_coverage_items,
            "error": error_message,
        },
    )


def get_severity_and_status(weighted_sum_of_errors, error_types):
    """
    Determines the severity, status, and reasons for the given weighted sum of errors and error types.

    Args:
        weighted_sum_of_errors (Decimal): The total weighted sum of errors calculated from the scores.
        error_types (list): A list of error types where the normalized score is below 0.5.

    Returns:
        tuple: A tuple containing the severity (str), status (str), and a list of reasons (str) for the errors.
    """
    reasons = []
    # Iterate over the severity thresholds
    for severity, threshold in SEVERITY_THRESHOLDS.items():
        if weighted_sum_of_errors <= threshold:
            # If the severity is "Low" and there are no errors in error_types
            # (i.e., error_types is empty), set status to "Approved"
            if severity == "Low" and not error_types:
                status = "Approved"
            else:
                status = "To Be Reviewed"

            # If error_types is not empty, provide reasons for the errors
            if error_types:
                verification_errors = {
                    "name_mismatch": "The name on the passport does not match the provided name.",
                    "not_authentic": "The passport uploaded is not authentic.",
                    "unrecognized": "The passport uploaded is not recognized.",
                    "expired_passport": "The passport is expired.",
                    "dob_mismatch": "The date of birth on the passport does not match the provided date of birth.",
                    "gender_mismatch": "The gender on the passport does not match the provided gender.",
                    "personal_details_flight_ticket_name_mismatch": "Name mismatch between personal details and flight ticket.",
                    "passport_flight_ticket_name_mismatch": "Name mismatch between passport and flight ticket.",
                    "incorrect_flight_ticket": "The uploaded flight ticket document is incorrect or cannot be read properly.",
                    "incorrect_baggage_tag": "The uploaded baggage tag document is incorrect or cannot be read properly.",
                    "airline_name_mismatch": "The airline name on the baggage tag does not match the airline name on the flight ticket.",
                    "booking_reference_mismatch": "The booking reference number on the baggage tag does not match the booking reference number on the flight ticket.",
                    "passenger_name_mismatch": "The passenger name on the baggage tag does not match the passenger name on the flight ticket.",
                    "invalid_emirates_barcode": "The barcode on the Emirates baggage tag is invalid.",
                }
                # Append the corresponding error descriptions to the reasons list
                for error in error_types:
                    reasons.append(verification_errors.get(error, ""))
            return severity, status, reasons


def claim_summary(request):
    """
    Handles the claim summary page, either saving claim data to the database and redirecting to claim success page (for POST requests),
    or displaying claim summary with customer details, claim details, and estimated gas fees (for GET requests).

    Args:
        request (HttpRequest): The request to the claim summary page.

    Returns:
        HttpResponse: Renders the claim summary page with customer and claim details, or redirects to the claim success page.
    """
    if request.method == "POST":
        if "submit-btn" in request.POST:
            # Get customer details from the session
            customer_details = request.session.get("personal_details", None)

            # Create new Customer instance and save to database
            customer = Customer(**customer_details)
            customer.save()

            # Get claim details from the session
            claim_details = request.session.get("claim_details", None)

            # Create new Claim instance
            claim = Claim(customer=customer, **claim_details)

            # Calculate severity and set claim status based on weighted_sum_of_errors
            weighted_sum_of_errors = Decimal(
                request.session.get("weighted_sum_of_errors", "0")
            )
            error_types = request.session.get("error_types", [])

            print(
                f"Weighted sum of errors in Claim Summary function: {weighted_sum_of_errors}"
            )
            print(f"Error Types in Claim Summary function: {error_types}")

            claim.severity, claim.status, claim.reasons = get_severity_and_status(
                weighted_sum_of_errors, error_types
            )

            # Convert reasons list to a string and save it
            claim.reasons = "; ".join(claim.reasons)

            # Save the claim to the database
            claim.save()

            # Add selected coverage items to the claim
            selected_coverage_items = request.session["coverage_items"]
            for item_name in selected_coverage_items:
                coverage_item = CoverageItem.objects.get(name=item_name)
                claim.coverage_items.add(coverage_item)

            # Save the claim with the associated coverage items
            claim.save()

            # Add claim to blockchain
            claim_data = {
                "id": claim.id,
                "customer_id": claim.customer.id,
                "date_of_loss": claim.date_of_loss,
                "description_of_loss": claim.description_of_loss,
                "claim_amount": str(claim.claim_amount),
                "created_on": claim.created_on.isoformat(),
                "country_of_incident": claim.country_of_incident,
            }
            add_claim_to_blockchain(claim_data)

            # Store claim ID in session
            request.session["claim_id"] = claim.id

            # Clear customer and claim details from session
            del request.session["personal_details"]
            del request.session["claim_details"]

            return redirect("claim_success")

    # If not POST, render the claim summary page with customer and claim details

    customer_details = request.session.get("personal_details", None)
    claim_details = request.session.get("claim_details", None)

    # Prepare the transaction
    transaction = prepare_claim_transaction(claim_details)

    # Estimate the gas required for the transaction
    estimated_gas = w3.eth.estimate_gas(transaction)

    # Calculate the gas fee
    adjusted_gas_price = transaction["maxFeePerGas"]
    gas_fee_wei = estimated_gas * adjusted_gas_price
    gas_fee_ether = w3.from_wei(gas_fee_wei, "ether")

    context = {
        "customer_details": customer_details,
        "claim_details": claim_details,
        "gas_fee": gas_fee_ether,
    }
    return render(request, "claim_summary.html", context)


def claim_success(request):
    claim_id = request.session["claim_id"]
    claim = Claim.objects.get(id=claim_id)
    customer = claim.customer
    return render(
        request,
        "success.html",
        {
            "claim": claim,
            "customer": customer,
            "claim_reference_number": claim.claim_reference_number,
        },
    )


@staff_member_required
def admin_view_claim(request):
    """
    Handles the admin view claim page, which allows staff members to view claim data from the blockchain.
    The claim data is retrieved using a POST request with a provided input_data_hex.

    Args:
        request (HttpRequest): The request to the admin view claim page.

    Returns:
        HttpResponse: Renders the admin view claim page with the decoded claim data.
    """
    claim_data = None

    if request.method == "POST":
        # Get the input_data_hex from the POST request
        input_data_hex = request.POST.get("input_data")

        # Remove the "0x" prefix from the input_data_hex if present
        if input_data_hex.startswith("0x"):
            input_data_hex = input_data_hex[2:]

        # Convert the input_data_hex to text
        input_data = Web3.to_text(hexstr=input_data_hex)

        # Try to parse the input_data as a JSON object
        try:
            claim_data = json.loads(input_data)
        except json.JSONDecodeError:
            claim_data = None

        if claim_data and isinstance(claim_data, dict):
            # Get block information
            block_number = claim_data.get("block_number", None)
            if block_number:
                # Retrieve the block from the blockchain using its block number
                block = w3.eth.get_block(block_number)

                # Add block hash and previous block hash to the claim_data dictionary
                claim_data["block_hash"] = block.hash.hex()
                claim_data["previous_block_hash"] = block.parentHash.hex()

            # Format the JSON object for better display (4 spaces indentation)
            claim_data = json.dumps(claim_data, indent=4)

    return render(request, "admin_view_claim.html", {"claim_data": claim_data})
