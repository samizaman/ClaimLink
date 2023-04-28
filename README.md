# ClaimLink

ClaimLink is a Django web application designed to manage insurance claims for customers. The application streamlines the process of submitting and verifying claims and provides a user-friendly interface for customers to manage their claims.

## Features

- Baggage tag extraction and validation
- Flight ticket extraction and validation
- Passport verification
- Insurance claims submission and management
- Admin panel for claims management
- Integration with Ethereum blockchain for claim storage and verification

## Configuration

Before running the application, you need to set up your `.env` file with the necessary API keys and configuration settings. Create a new file named `.env` in the root directory of the project and add the following variables:

```plaintext
ACCOUNT_ADDRESS=
PRIVATE_KEY=
INFURA_PROJECT_ID=

IDANALYZER_API_KEY=

AWS_ACCESS_KEY=
AWS_SECRET_KEY=
```
Fill in the appropriate values for each variable:

ACCOUNT_ADDRESS: Your Ethereum wallet address.
PRIVATE_KEY: The private key associated with your Ethereum wallet address.
INFURA_PROJECT_ID: Your Infura project ID for accessing the Ethereum network.
IDANALYZER_API_KEY: Your API key for the ID Analyzer service.
AWS_ACCESS_KEY: Your AWS access key for accessing AWS services (e.g., S3).
AWS_SECRET_KEY: Your AWS secret key for accessing AWS services (e.g., S3).

Save the file and make sure it is gitignored to avoid accidentally committing sensitive information to the repository.

## Installation

1. Ensure you have Python 3.10 installed on your machine.

2. Clone the repository to your local machine:
``
git clone https://github.com/samizaman/ClaimLink.git
``
3. Navigate to the project directory:
``
cd ClaimLink
``
4. Create a virtual environment:
``
python3 -m venv venv
``
5. Activate the virtual environment:
``
source venv/bin/activate
``
6. Install the project dependencies:
``
pip install -r requirements.txt
``
7. Apply database migrations:
``
python manage.py migrate
``
8. Run the initialize_data.py script to set up initial data:
``
python initialize_data.py
``
9. Run the development server:
``
python manage.py runserver
``


## Contributing

We welcome contributions to ClaimLink! Feel free to open issues or submit pull requests with any improvements, bug fixes, or suggestions. We appreciate your help in making this project better!

## License

This project is released under the MIT License. See the `LICENSE` file for more details.



