# ClaimLink

ClaimLink is a Django web application designed to manage insurance claims for customers. The application streamlines the process of submitting and verifying claims and provides a user-friendly interface for customers to manage their claims.

## Features

- Baggage tag extraction and validation
- Flight ticket extraction and validation
- Passport verification
- Insurance claims submission and management
- Admin panel for claims management

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



