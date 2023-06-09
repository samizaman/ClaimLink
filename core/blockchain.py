import json
import os
from datetime import datetime

from django.utils import timezone
from dotenv import load_dotenv
from web3 import Web3

from core.models import (
    Block,
    Blockchain,
    Claim,
    Customer,
)

load_dotenv()

goerli_url = f"https://goerli.infura.io/v3/{os.getenv('INFURA_PROJECT_ID')}"
w3 = Web3(Web3.HTTPProvider(goerli_url))


def prepare_claim_transaction(claim):
    """
    Prepare a transaction to add a claim to the Ethereum blockchain.

    Args:
        claim (dict): The claim data as a dictionary.

    Returns:
        dict: A dictionary containing the prepared transaction details.
    """
    account_address = os.getenv("ACCOUNT_ADDRESS")

    # Fetch the current gas price from the Ethereum network
    current_gas_price = w3.eth.gas_price
    gas_price_multiplier = 1.2  # Adjust this value as needed
    adjusted_gas_price = int(current_gas_price * gas_price_multiplier)

    # Get the chain ID
    chain_id = w3.eth.chain_id

    # Set up the transaction details
    transaction = {
        "to": account_address,  # The destination address of the transaction
        "value": w3.to_wei(
            0, "ether"
        ),  # The amount of Ether being transferred (0 in this case)
        "maxFeePerGas": adjusted_gas_price,  # The maximum fee per gas unit for the transaction
        "maxPriorityFeePerGas": adjusted_gas_price,  # The maximum priority fee per gas unit for the transaction
        "nonce": w3.eth.get_transaction_count(
            w3.to_checksum_address(account_address)
        ),  # The nonce of the sender's account, which is the number of transactions sent from the account
        "chainId": chain_id,  # The chain ID of the Ethereum network being used
        "data": w3.to_hex(
            json.dumps(claim).encode("utf-8")
        ),  # The data being sent with the transaction, in this case, the claim details serialized and encoded as a hex string
    }

    return transaction


def add_claim_to_blockchain(claim):
    """
    Add a claim to the Ethereum blockchain.

    Args:
        claim (dict): The claim data as a dictionary.

    Returns:
        bool: True if the claim was successfully added to the blockchain, False otherwise.
    """
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
        # We wait because the process of mining confirms the transaction, ensuring
        # its validity and security within the Ethereum network. Until a transaction is mined and included in a block,
        # it is considered unconfirmed and its finality is uncertain. By waiting for the transaction to be mined, we can
        # confirm its success and proceed with any follow-up actions, such as saving the block information to the database.
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
