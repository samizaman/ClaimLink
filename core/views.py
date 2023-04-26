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
from core.passport_verification import is_passport_fraud
from .baggage_tag_extractor.baggage_tag import process_baggage_tag_image
from .blockchain import add_claim_to_blockchain, prepare_claim_transaction
from .flight_ticket_extractor.flight_ticket_info_extractor import extract_ticket_info
from .forms import (
    ClaimDetailsForm,
    CoverageItemsSelectionForm,
    PersonalDetailsForm,
    RequiredDocumentsForm,
)

load_dotenv()

goerli_url = f"https://goerli.infura.io/v3/{os.getenv('INFURA_PROJECT_ID')}"
w3 = Web3(Web3.HTTPProvider(goerli_url))
SEVERITY_THRESHOLDS = {
    "Low": Decimal("90"),
    "Medium": Decimal("75"),
    "High": Decimal("0"),
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


def create_rejected_claim(customer, reason):
    claim = Claim(
        customer=customer,
        status="rejected",
        reasons=reason,
    )
    claim.save()
    return claim


def process_flight_ticket(flight_ticket):
    flight_ticket_path = default_storage.save(
        f"temp/{flight_ticket.name}", flight_ticket
    )
    flight_ticket_temp_path = default_storage.path(flight_ticket_path)

    extracted_flight_data = extract_ticket_info(flight_ticket_temp_path)
    os.remove(flight_ticket_temp_path)
    return extracted_flight_data


def process_baggage_tag(baggage_tag):
    baggage_tag_path = default_storage.save(f"temp/{baggage_tag.name}", baggage_tag)
    baggage_tag_temp_path = default_storage.path(baggage_tag_path)

    extracted_baggage_data = process_baggage_tag_image(baggage_tag_temp_path)
    os.remove(baggage_tag_temp_path)
    return extracted_baggage_data


def normalize_score(score, min_score, max_score):
    """
    The normalize_score function takes a score and its minimum and maximum possible values,
    then scales the score to a range between 0 and 1.

    :param score: The score to be normalized
    :param min_score: The minimum possible value of the score
    :param max_score: The maximum possible value of the score
    :return: The normalized score
    """
    return (score - min_score) / (max_score - min_score)


def calculate_composite_score(passport_scores):
    """
    The calculate_composite_score function takes a dictionary of passport_scores and calculates
    a composite score by normalizing the individual scores and then averaging them.

    :param passport_scores: A dictionary containing the scores to be combined
    :return: The calculated composite score
    """
    # Define the minimum and maximum score possible for each individual score
    min_score = 0
    max_score = 100

    # Normalize the scores using the normalize_score function, and create a list of normalized scores
    normalized_scores = [
        normalize_score(score, min_score, max_score)
        for score in passport_scores.values()
    ]

    # Calculate the composite score by taking the average of the normalized scores
    composite_score = sum(normalized_scores) / len(normalized_scores)

    return composite_score


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

    passport_scores = is_passport_fraud(passport_actual_path, user_data)
    print(f"Passport scores: {passport_scores}")

    # Calculate the composite score
    composite_score = calculate_composite_score(passport_scores)
    print(f"Composite score: {composite_score}")

    # You may still want to identify which errors occurred, if any, for providing detailed feedback
    error_types = [key for key, value in passport_scores.items() if value > 0]

    return composite_score, error_types


def required_documents(request):
    selected_coverage_items = request.session.get("coverage_items", [])

    if request.method == "POST":
        form = RequiredDocumentsForm(request.POST, request.FILES)
        if form.is_valid():
            flight_ticket = form.cleaned_data["flight_ticket"]
            baggage_tag = form.cleaned_data.get("baggage_tag", None)
            passport = form.cleaned_data["passport"]

            extracted_flight_data = process_flight_ticket(flight_ticket)
            if extracted_flight_data:
                print("\nExtracted flight data:")
                for key, value in extracted_flight_data.items():
                    print(f"{key}: {value}")

            if baggage_tag:
                extracted_baggage_data = process_baggage_tag(baggage_tag)
                if extracted_baggage_data:
                    print("\nExtracted baggage data:")
                    for key, value in extracted_baggage_data.items():
                        print(f"{key}: {value}")

            if passport:
                composite_score, error_types = process_passport(passport, request)
                print(f"Composite Score in Required Documents: {composite_score}")
                print(f"Error Types in Required Documents: {error_types}")
                request.session["composite_score"] = str(composite_score)
                request.session["error_types"] = error_types

                return redirect("claim_summary")

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


def get_severity_and_status(score, error_types):
    reasons = []
    for severity, threshold in SEVERITY_THRESHOLDS.items():
        if score >= threshold:
            # If the severity is "Low" and there are no errors in error_types
            # (i.e., error_types is empty), set status to "Approved"
            if severity == "Low" and not error_types:
                status = "Approved"
            elif score < Decimal("50"):
                status = "Rejected"
            else:
                status = "To Be Reviewed"

            if error_types:
                passport_verification_errors = {
                    "name_mismatch": "The name on the passport does not match the provided name.",
                    "not_authentic": "The passport uploaded is not authentic.",
                    "unrecognized": "The passport uploaded is not recognized. Please upload a clear and fully visible image.",
                    "expired_passport": "The passport is expired.",
                    "dob_mismatch": "The date of birth on the passport does not match the provided date of birth.",
                    "gender_mismatch": "The gender on the passport does not match the provided gender.",
                }
                for error in error_types:
                    reasons.append(passport_verification_errors.get(error, ""))
            return severity, status, reasons


def claim_summary(request):
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

            # Calculate severity and set claim status based on composite score
            composite_score = Decimal(request.session.get("composite_score", "0"))
            error_types = request.session.get("error_types", [])

            print(f"Composite Score in Claim Summary function: {composite_score}")
            print(f"Error Types in Claim Summary function: {error_types}")

            claim.severity, claim.status, claim.reasons = get_severity_and_status(
                composite_score, error_types
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
    claim_data = None

    if request.method == "POST":
        input_data_hex = request.POST.get("input_data")
        if input_data_hex.startswith("0x"):
            input_data_hex = input_data_hex[2:]
        input_data = Web3.to_text(hexstr=input_data_hex)

        try:
            claim_data = json.loads(input_data)
        except json.JSONDecodeError:
            claim_data = None

        if claim_data and isinstance(claim_data, dict):
            # Get block information
            block_number = claim_data.get("block_number", None)
            if block_number:
                block = w3.eth.get_block(block_number)
                claim_data["block_hash"] = block.hash.hex()
                claim_data["previous_block_hash"] = block.parentHash.hex()

            # Format the JSON object for better display (4 spaces indentation)
            claim_data = json.dumps(claim_data, indent=4)

    return render(request, "admin_view_claim.html", {"claim_data": claim_data})
