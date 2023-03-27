import json
import os
from datetime import datetime

from django.core.files.storage import default_storage
from django.shortcuts import redirect, render
from django.utils import timezone
from dotenv import load_dotenv
from web3 import Web3

from core.models import (
    Block,
    Blockchain,
    Claim,
    COUNTRY_CHOICES,
    CoverageItem,
    CURRENCY_CHOICES,
    Customer,
)
from core.utils import is_passport_fraud
from .forms import PersonalDetailsForm

load_dotenv()

goerli_url = f"https://goerli.infura.io/v3/{os.getenv('INFURA_PROJECT_ID')}"
w3 = Web3(Web3.HTTPProvider(goerli_url))


def add_claim_to_blockchain(claim):
    account_address = os.getenv("ACCOUNT_ADDRESS")
    private_key = os.getenv("PRIVATE_KEY")

    # Check if connected to Ethereum network
    if not w3.isConnected():
        print("Error: Could not connect to the Ethereum network.")
        return False

    # Set up the transaction details
    transaction = {
        "to": account_address,
        "value": w3.toWei(0, "ether"),
        "gas": 210000,
        "gasPrice": w3.toWei("140", "gwei"),
        "nonce": w3.eth.getTransactionCount(account_address),
        "data": w3.toHex(json.dumps(claim).encode("utf-8")),
    }

    # Sign the transaction
    signed_transaction = w3.eth.account.signTransaction(transaction, private_key)

    # Send the transaction
    transaction_hash = w3.eth.sendRawTransaction(signed_transaction.rawTransaction)
    try:
        # Wait for the transaction to be mined
        transaction_receipt = w3.eth.waitForTransactionReceipt(transaction_hash)
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
            block = w3.eth.getBlock(block_number)
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
    form = PersonalDetailsForm()

    if request.method == "POST":
        form = PersonalDetailsForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            phone_number = form.cleaned_data["phone_number"]
            dob = form.cleaned_data["dob"]
            gender = form.cleaned_data["gender"]

            request.session["customer_details"] = {
                "name": name,
                "email": email,
                "phone_number": phone_number,
                "dob": dob,
                "gender": gender,
            }

            return redirect("claim_details")

    return render(request, "personal_details.html", {"form": form})


def claim_details(request):
    if request.method == "POST":
        if "next-coverage-items" in request.POST:
            # Extract claim details from POST request
            date_of_loss = request.POST.get("date_of_loss")
            description_of_loss = request.POST.get("description_of_loss")
            # passport = request.FILES.get("passport")
            claim_amount = request.POST.get("claim_amount")
            country_of_incident = request.POST.get("country_of_incident")
            claim_amount_currency = request.POST.get("claim_amount_currency")

            # Store claim details in session
            request.session["claim_details"] = {
                "date_of_loss": date_of_loss,
                "description_of_loss": description_of_loss,
                # "passport": passport_path,
                "claim_amount": claim_amount,
                "country_of_incident": country_of_incident,
                "claim_amount_currency": claim_amount_currency,
            }

            return redirect("coverage_items_selection")

    return render(
        request,
        "claim_details.html",
        {"COUNTRY_CHOICES": COUNTRY_CHOICES, "CURRENCY_CHOICES": CURRENCY_CHOICES},
    )


def coverage_items_selection(request):
    if request.method == "POST":
        if "next-required-documents" in request.POST:
            coverage_items = request.POST.getlist("coverage_items")
            request.session["coverage_items"] = coverage_items
            return redirect("required_documents")

    # Load previously selected coverage items from session
    selected_coverage_items = request.session.get("coverage_items", [])
    print(f"Selected coverage items: {selected_coverage_items}")

    return render(
        request,
        "coverage_items_selection.html",
        {"selected_coverage_items": selected_coverage_items},
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
        if "next-claim-summary" in request.POST:

            passport = request.FILES.get("passport", None)
            travel_documents = request.FILES.get("travel_documents", None)

            passport_verification_error = ""

            if passport and travel_documents:
                passport_path = default_storage.save(
                    f"passport_photos/{passport.name}", passport
                )
                travel_documents_path = default_storage.save(
                    "travel_documents/" + travel_documents.name, travel_documents
                )

                passport_actual_path = default_storage.path(passport_path)

                # Retrieve the user's name from the session
                customer_details = request.session.get("customer_details", None)
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

            else:
                return render(
                    request,
                    "required_documents.html",
                    {"error": "Both passport and travel documents are required."},
                )

    return render(
        request,
        "required_documents.html",
        {"selected_coverage_items": selected_coverage_items},
    )


def claim_summary(request):
    if request.method == "POST":
        if "submit-btn" in request.POST:
            # Get customer details from the session
            customer_details = request.session["customer_details"]

            # Create new Customer instance and save to database
            customer = Customer(**customer_details)
            customer.save()

            # Get claim details from the session
            claim_details = request.session["claim_details"]

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
            del request.session["customer_details"]
            del request.session["claim_details"]

            return redirect("claim_success")

    # If not POST, render the claim summary page with customer and claim details

    gas_price = Web3.toWei("140", "gwei")
    gas_limit = 210000
    gas_fee = gas_price * gas_limit

    gas_fee_ether = Web3.fromWei(gas_fee, "ether")

    customer_details = request.session["customer_details"]
    claim_details = request.session["claim_details"]

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


def view_claim(request):
    claim_data = None

    if request.method == "POST":
        input_data_hex = request.POST.get("input_data")
        if input_data_hex.startswith("0x"):
            input_data_hex = input_data_hex[2:]
        input_data = Web3.toText(hexstr=input_data_hex)

        try:
            claim_data = json.loads(input_data)
        except json.JSONDecodeError:
            claim_data = None

        if claim_data and isinstance(claim_data, dict):
            # Get block information
            block_number = claim_data.get("block_number", None)
            if block_number:
                block = w3.eth.getBlock(block_number)
                claim_data["block_hash"] = block.hash.hex()
                claim_data["previous_block_hash"] = block.parentHash.hex()

            # Format the JSON object for better display (4 spaces indentation)
            claim_data = json.dumps(claim_data, indent=4)

    return render(request, "view_claim.html", {"claim_data": claim_data})
