import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "claimlink.settings")
django.setup()

from core.models import CoverageItem, Blockchain

def create_coverage_items():
    coverage_items = [
        "Flight Delay or Abandonment",
        "Baggage Delay",
        "Baggage Loss",
    ]

    for item_name in coverage_items:
        coverage_item, created = CoverageItem.objects.get_or_create(name=item_name)
        if created:
            print(f"Created coverage item: {item_name}")
        else:
            print(f"Coverage item already exists: {item_name}")

def create_blockchains():
    goerli_blockchain, created = Blockchain.objects.get_or_create(
        network_name="Goerli Testnet",
        network_url="https://goerli.infura.io/v3/0f045722b7a548d7b170dd4ae314ff3d",
    )

    if created:
        print("Created Goerli Testnet blockchain")
    else:
        print("Goerli Testnet blockchain already exists")

def main():
    create_coverage_items()
    create_blockchains()

if __name__ == "__main__":
    main()
