from unittest import TestCase
from unittest import TestCase
from unittest.mock import patch

from core.blockchain import prepare_claim_transaction
from core.models import Block, Blockchain, Claim, Customer


class BlockchainTestCase(TestCase):
    def setUp(self):
        goerli_testnet = Blockchain.objects.filter(
            network_name="Goerli Testnet"
        ).first()
        if goerli_testnet:
            Block.objects.filter(blockchain=goerli_testnet).delete()
            goerli_testnet.delete()
        self.blockchain = Blockchain.objects.create(
            network_name="Goerli Testnet",
            network_url="https://goerli.infura.io/v3/YOUR_API_KEY",
        )
        self.customer = Customer.objects.create(
            name="John Doe", email="john.doe@example.com", phone_number="1234567890"
        )
        self.claim = Claim.objects.create(
            customer=self.customer,
            date_of_loss="2022-01-01",
            country_of_incident="US",
            description_of_loss="Test description of loss",
            claim_amount=1000,
        )

    @patch("core.blockchain.w3")
    def test_prepare_claim_transaction(self, mock_w3):
        mock_w3.eth.gas_price = 100
        mock_w3.eth.chain_id = 5
        mock_w3.eth.get_transaction_count.return_value = 0

        claim_data = {
            "id": self.claim.id,
            "customer_id": self.customer.id,
            "date_of_loss": str(self.claim.date_of_loss),
            "country_of_incident": self.claim.country_of_incident,
            "description_of_loss": self.claim.description_of_loss,
            "claim_amount": self.claim.claim_amount,
        }

        transaction = prepare_claim_transaction(claim_data)
        self.assertIsInstance(transaction, dict)
        self.assertIn("to", transaction)
        self.assertIn("value", transaction)
        self.assertIn("maxFeePerGas", transaction)
        self.assertIn("maxPriorityFeePerGas", transaction)
        self.assertIn("nonce", transaction)
        self.assertIn("chainId", transaction)
        self.assertIn("data", transaction)
