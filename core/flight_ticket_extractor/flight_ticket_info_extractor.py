import os
import re
from datetime import datetime

import cv2
import numpy as np
from pdf2image import convert_from_path

from core.common.extractor_utils import (
    extract_text,
    load_config,
    setup_textract_client,
)

USE_AWS = True  # Set to False when you don't want to Free Tier credits
TICKET_TYPE_KEYWORDS = {
    "emirates": "Emirates",
    "flynas": "Flynas",
}


def convert_pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path, first_page=0, last_page=1)
    return images


def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray


def process_name_emirates(name_parts):
    if len(name_parts) == 2:
        last_name, first_name_and_salutation = name_parts
        salutation = first_name_and_salutation[-2:].upper()
        first_name = first_name_and_salutation[:-2]
    else:
        salutation = ""
        first_name = ""
        last_name = ""
    return salutation, first_name, last_name


def process_name_flynas(name_parts):
    if len(name_parts) == 3:
        salutation, first_name, last_name = name_parts
    else:
        salutation = ""
        first_name = ""
        last_name = ""
    return salutation, first_name, last_name


def process_name(region_name, text, ticket_type=None):
    name_parts = re.split(r"\s|/", text)

    ticket_type_processors = {
        "emirates": process_name_emirates,
        "flynas": process_name_flynas,
    }

    if ticket_type in ticket_type_processors:
        salutation, first_name, last_name = ticket_type_processors[ticket_type](
            name_parts
        )
    else:
        salutation = ""
        first_name = ""
        last_name = ""

    return {
        "salutation": salutation,
        "first_name": first_name,
        "last_name": last_name,
    }


def process_date(region_name, text, ticket_type=None):
    date_formats = ["%d%b%Y", "%A %d %B %Y", "%d %b %y"]

    for date_format in date_formats:
        try:
            date_obj = datetime.strptime(text, date_format)
            formatted_date = date_obj.strftime("%d-%m-%Y")
            return {region_name: formatted_date}
        except ValueError:
            continue

    return {region_name: None}


def process_booking_reference_number(region_name, text, ticket_type=None):
    if len(text) != 6 or not text.isalnum():
        return {region_name: None}
    return {region_name: text.strip()}


def process_airline_name(region_name, text, ticket_type=None):
    if not text.isalnum() or len(text) < 4:
        return {region_name: None}
    return {region_name: text.strip()}


def validate_coordinates(image, region_coordinates):
    """
    Validate whether the given region coordinates are within the image boundaries.

    :param image: ndarray, input image
    :param region_coordinates: tuple, (x, y, w, h) region coordinates
    :return: bool, True if the coordinates are valid, False otherwise
    """
    x, y, w, h = region_coordinates
    height, width = image.shape[:2]

    if x < 0 or y < 0 or x + w > width or y + h > height:
        return False
    return True


def process_text(region_name, text, processing_function, ticket_type=None):
    """
    Process the extracted text using the specified processing_function.

    :param region_name: str, name of the region in the configuration file
    :param text: str, extracted text from the region
    :param processing_function: function, function to process the text (if required)
    :param ticket_type: str, type of the ticket (e.g., 'flight', 'baggage')
    :return: dict, processed text as a key-value pair
    """
    text = text.strip()
    if not text:
        return {region_name: None}

    if processing_function:
        return processing_function(region_name, text, ticket_type)
    else:
        return {region_name: text.strip()}


def process_document(image, config, textract_client, ticket_type=None):
    """
    Process the document image using the given configuration, extracting text from specified regions.

    :param image: ndarray, input image
    :param config: dict, configuration for the document processing
    :param textract_client: boto3 Textract client, used for extracting text from the image
    :param ticket_type: str, type of the ticket (e.g., 'flight', 'baggage')
    :return: dict, extracted and processed data from the image
    """
    preprocessed_image = preprocess_image(image)
    extracted_data = {}

    for region_name, region_info in config["regions"].items():
        region_coordinates = region_info["coordinates"]
        processing_function_name = region_info.get("processing_function")
        processing_function = None

        if processing_function_name:
            processing_functions = {
                "process_name": process_name,
                "process_date": process_date,
                "process_booking_reference_number": process_booking_reference_number,
                "process_airline_name": process_airline_name,
            }
            processing_function = processing_functions.get(processing_function_name)

        if validate_coordinates(preprocessed_image, region_coordinates):
            text = extract_text(
                image=image,
                region_coordinates=region_coordinates,
                textract_client=textract_client,
                use_aws=USE_AWS,
            )
            processed_data = process_text(
                region_name, text, processing_function, ticket_type
            )

            if ticket_type is None and region_name == "flight_name":
                if "Emirates" in text:
                    ticket_type = "emirates"
                elif "Flynas" in text:
                    ticket_type = "flynas"

        else:
            print(f"Invalid coordinates for region: {region_name}")
            processed_data = {region_name: None}

        extracted_data.update(processed_data)

    return extracted_data


def read_image(file_path, file_extension):
    """
    Read the image from the given file path with the specified file extension.

    :param file_path: str, path to the input image file
    :param file_extension: str, file extension of the input image
    :return: ndarray, image or None if the image could not be read
    """
    if file_extension == ".pdf":
        images = convert_pdf_to_images(file_path)
        if images:
            image = images[0]
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            print("No images found in the PDF.")
            return None
    else:
        try:
            return cv2.imread(file_path)
        except Exception as e:
            print(f"Error reading the input image: {e}")
            return None


def load_and_process_config(image, textract_client, ticket_type):
    """
    Load the configuration file for the given ticket type and process the image using the configuration.

    :param image: ndarray, input image
    :param textract_client: boto3 Textract client, used for extracting text from the image
    :param ticket_type: str, type of the ticket (e.g., 'flight', 'baggage')
    :return: dict, extracted ticket information
    """
    if image is not None:
        config_filename = f"{ticket_type}_ticket_config.json"
        config_path = os.path.join(
            os.path.dirname(__file__), "configs", config_filename
        )
        config = load_config(config_path)
        if config is None:
            print(
                "Error loading the configuration file. Please check the file path and format."
            )
            return None
        return process_document(image, config, textract_client, ticket_type)
    else:
        print("Error reading the input image.")
        return None


def determine_ticket_type(image, textract_client):
    """
    Determine the type of the ticket from the given image using a predefined set of keywords.

    :param image: ndarray, input image
    :param textract_client: boto3 Textract client, used for extracting text from the image
    :return: str, ticket type (e.g., 'flight', 'baggage') or None if the ticket type could not be determined
    """
    if image is not None:
        text = extract_text(
            image=image,
            region_coordinates=[0, 0, image.shape[1], image.shape[0]],
            textract_client=textract_client,
            use_aws=USE_AWS,
        )
        for ticket_type, keyword in TICKET_TYPE_KEYWORDS.items():
            if keyword in text:
                return ticket_type
    return None


def extract_ticket_info(file_path):
    """
    Extract ticket information from the given file path.

    :param file_path: str, path to the input image file
    :return: dict, extracted ticket information or None if the ticket type could not be determined
    """
    textract_client = setup_textract_client(
        access_key=os.getenv("AWS_ACCESS_KEY"), secret_key=os.getenv("AWS_SECRET_KEY")
    )

    file_extension = os.path.splitext(file_path)[1].lower()
    image = read_image(file_path, file_extension)

    # Determine the ticket type
    ticket_type = determine_ticket_type(image, textract_client)
    if ticket_type is None:
        print("Error: Could not determine ticket type.")
        return None

    # Load and process the configuration for the determined ticket type
    extracted_data = load_and_process_config(image, textract_client, ticket_type)
    return extracted_data
