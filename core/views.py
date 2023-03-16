import json
import os

from django.shortcuts import redirect, render
from dotenv import load_dotenv
from web3 import Web3

from core.models import Claim, Customer

load_dotenv()


def add_claim_to_blockchain(claim):
    goerli_url = "https://goerli.infura.io/v3/0f045722b7a548d7b170dd4ae314ff3d"
    w3 = Web3(Web3.HTTPProvider(goerli_url))

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
        "gasPrice": w3.toWei("50", "gwei"),
        "nonce": w3.eth.getTransactionCount(account_address),
        "data": w3.toHex(json.dumps(claim).encode("utf-8")),
    }

    # Sign the transaction
    signed_transaction = w3.eth.account.signTransaction(transaction, private_key)

    # Send the transaction
    transaction_hash = w3.eth.sendRawTransaction(signed_transaction.rawTransaction)

    # Wait for the transaction to be mined
    transaction_receipt = w3.eth.waitForTransactionReceipt(transaction_hash)

    # Check if the transaction was successful
    if transaction_receipt["status"]:
        print(
            f"Transaction was successfully added to the blockchain with hash {transaction_hash.hex()}"
        )
        return True
    else:
        print("Transaction failed.")
        return False


def home(request):
    return render(request, "home.html")


def personal_details(request):
    if request.method == "POST":
        if "next-claims-details" in request.POST:
            # Extract personal details from POST request
            name = request.POST.get("name")
            email = request.POST.get("email")
            phone_number = request.POST.get("phone_number", "")
            dob = request.POST.get("dob")
            gender = request.POST.get("gender")

            # Create new Customer instance and save to database
            customer = Customer(
                name=name,
                email=email,
                phone_number=phone_number,
                dob=dob,
                gender=gender,
            )
            customer.save()

            # Store customer ID in session
            request.session["customer_id"] = customer.id

            return redirect("claim_details")

    return render(request, "personal_details.html")


def claim_details(request):
    if request.method == "POST":
        if "submit-btn" in request.POST:
            # Extract claim details from POST request
            date_of_loss = request.POST.get("date_of_loss")
            description_of_loss = request.POST.get("description_of_loss")
            passport = request.FILES.get("passport")
            claim_amount = request.POST.get("claim_amount")

            # Get customer ID from session
            customer_id = request.session["customer_id"]

            # Create new Claim instance and save to database
            customer = Customer.objects.get(id=customer_id)

            claim = Claim(
                customer=customer,
                date_of_loss=date_of_loss,
                description_of_loss=description_of_loss,
                passport=passport,
                claim_amount=claim_amount,
            )
            claim.save()

            # Add claim to blockchain
            claim_data = {
                "id": claim.id,
                "customer_id": claim.customer.id,
                "date_of_loss": claim.date_of_loss,
                "description_of_loss": claim.description_of_loss,
                "claim_amount": str(claim.claim_amount),
                "created_on": claim.created_on.isoformat(),
            }
            add_claim_to_blockchain(claim_data)

            # Store claim ID in session
            request.session["claim_id"] = claim.id

            # Clear customer ID from session
            del request.session["customer_id"]

            return redirect("claim_success")

    return render(request, "claim_details.html")


def claim_success(request):
    claim_id = request.session["claim_id"]
    claim = Claim.objects.get(id=claim_id)
    customer = claim.customer
    return render(request, "success.html", {"claim": claim, "customer": customer})


def view_claim(request):
    # Initialize claim_data variable to store claim information
    claim_data = None

    # Check if the request method is POST
    if request.method == "POST":
        # Get the input_data from the POST request
        input_data_hex = request.POST.get("input_data")

        # Remove "0x" prefix from the input data if it exists
        if input_data_hex.startswith("0x"):
            input_data_hex = input_data_hex[2:]

        # Convert the input data from hex to text
        input_data = Web3.toText(hexstr=input_data_hex)

        # Load the input data as a JSON object
        claim_data = json.loads(input_data)

        # Format the JSON object for better display (4 spaces indentation)
        claim_data = json.dumps(claim_data, indent=4)

    # Render the view_claim.html template with the claim_data context
    return render(request, "view_claim.html", {"claim_data": claim_data})
