import json
import os
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.shortcuts import redirect, render
from django.utils import timezone
from dotenv import load_dotenv
from web3 import Web3

from core.models import (
    Block,
    Blockchain,
    Claim,
    CoverageItem,
    Customer,
)
from core.utils import is_passport_fraud
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


def prepare_claim_transaction(claim):
    account_address = os.getenv("ACCOUNT_ADDRESS")

    # Fetch the current gas price from the Ethereum network
    current_gas_price = w3.eth.gas_price
    gas_price_multiplier = 1.2  # Adjust this value as needed
    adjusted_gas_price = int(current_gas_price * gas_price_multiplier)

    # Get the chain ID
    chain_id = w3.eth.chain_id

    # Set up the transaction details
    transaction = {
        "to": account_address,
        "value": w3.to_wei(0, "ether"),
        "maxFeePerGas": adjusted_gas_price,
        "maxPriorityFeePerGas": adjusted_gas_price,
        "nonce": w3.eth.get_transaction_count(w3.to_checksum_address(account_address)),
        "chainId": chain_id,
        "data": w3.to_hex(json.dumps(claim).encode("utf-8")),
    }

    return transaction


def add_claim_to_blockchain(claim):
    private_key = os.getenv("PRIVATE_KEY")

    # Check if connected to Ethereum network
    if not w3.is_connected():
        print("Error: Could not connect to the Ethereum network.")
        return False

    # Set up the transaction details
    transaction = prepare_claim_transaction(claim)

    # Estimate the gas required for the transaction
    transaction["gas"] = w3.eth.estimate_gas(transaction)
    print(f"Estimated gas required: {transaction['gas']}")

    # Sign the transaction
    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)

    # Send the transaction
    transaction_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    try:
        # Wait for the transaction to be mined
        transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
    except Exception as e:
        print("Error while waiting for transaction receipt:", e)
        return False

    # Check if the transaction was successful
    if transaction_receipt["status"]:
        print(
            f"Transaction was successfully added to the blockchain. View the transaction at https://goerli.etherscan.io/tx/{transaction_hash.hex()}"
        )
        # Get the block number from the transaction receipt
        block_number = transaction_receipt["blockNumber"]

        try:
            # Retrieve the block information
            block = w3.eth.get_block(block_number)
        except Exception as e:
            print("Error while retrieving block information:", e)
            return False

        # Get the customer instance using the customer_id
        customer = Customer.objects.get(id=claim["customer_id"])
        claim = Claim.objects.get(id=claim["id"])

        # Create and save the Block instance
        goerli = Blockchain.objects.get(network_name="Goerli Testnet")
        block_instance = Block(
            blockchain=goerli,
            customer=customer,
            claim=claim,
            block_number=block_number,
            block_hash=block["hash"].hex(),
            previous_block_hash=block["parentHash"].hex(),
            timestamp=timezone.make_aware(datetime.fromtimestamp(block["timestamp"])),
        )
        block_instance.save()

        return True
    else:
        print("Transaction failed.")
        return False


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


def required_documents(request):
    selected_coverage_items = request.session.get("coverage_items", [])

    if request.method == "POST":
        form = RequiredDocumentsForm(request.POST, request.FILES)
        if form.is_valid():
            passport = form.cleaned_data["passport"]
            flight_ticket = form.cleaned_data["flight_ticket"]
            baggage_tag = form.cleaned_data.get("baggage_tag", None)

            # Save the uploaded flight_ticket to a temporary location
            flight_ticket_path = default_storage.save(
                f"temp/{flight_ticket.name}", flight_ticket
            )
            flight_ticket_temp_path = default_storage.path(flight_ticket_path)

            extracted_data = extract_ticket_info(flight_ticket_temp_path)
            # Print the extracted data
            print("Extracted data:")
            for key, value in extracted_data.items():
                print(f"{key}: {value}")

            # Remove the temporary flight_ticket file after processing
            os.remove(flight_ticket_temp_path)

            # Your existing logic for processing the uploaded files...
            passport_verification_error = ""

            if passport:
                passport_path = default_storage.save(
                    f"passport_photos/{passport.name}", passport
                )
                # travel_documents_path = default_storage.save(
                #     "travel_documents/" + travel_documents.name, travel_documents
                # )

                passport_actual_path = default_storage.path(passport_path)

                # Retrieve the user's name from the session
                customer_details = request.session.get("personal_details", None)
                print(customer_details)
                if customer_details:
                    user_data = {
                        "name": customer_details.get("name", ""),
                        "dob": customer_details.get("dob", ""),
                        "gender": customer_details.get("gender", ""),
                    }
                else:
                    # Handle the case when customer_details is not available in the session
                    print("Customer details not found in the session.")
                    user_data = {"name": "", "dob": "", "gender": ""}

                # Check if the passport is a fraud
                passport_status = is_passport_fraud(passport_actual_path, user_data)
                passport_verification_errors = {
                    "name_mismatch": "The name on the passport does not match the provided name.",
                    "not_authentic": "The passport uploaded is not authentic.",
                    "unrecognized": "The passport uploaded is not recognized. Please upload a clear and fully visible image.",
                    "expired_passport": "The passport is expired.",
                    "dob_mismatch": "The date of birth on the passport does not match the provided date of birth.",
                    "gender_mismatch": "The gender on the passport does not match the provided gender.",
                }

                if passport_status:
                    passport_verification_error = "; ".join(
                        [
                            passport_verification_errors.get(status, "")
                            for status in passport_status
                        ]
                    )
                    print(f"Passport Verification Error: {passport_verification_error}")

                request.session[
                    "passport_verification_error"
                ] = passport_verification_error
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

            # Check if any passport checks failed
            passport_verification_error = request.session.get(
                "passport_verification_error", ""
            )

            if passport_verification_error:
                # Update claim status and reasons
                claim.status = "rejected"
                claim.reasons = passport_verification_error

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
