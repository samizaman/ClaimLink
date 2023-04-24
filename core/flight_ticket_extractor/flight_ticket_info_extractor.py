import io
import json
import os
import re
from datetime import datetime

import boto3
import cv2
import numpy as np
from botocore.exceptions import ClientError
from pdf2image import convert_from_path


def convert_pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path, first_page=0, last_page=1)
    return images


def load_config(config_path):
    try:
        with open(config_path, "r") as config_file:
            config_data = json.load(config_file)
        return config_data
    except Exception as e:
        print(f"Error loading configuration file: {e}")
        return None


def setup_textract_client(access_key, secret_key):
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-west-2",
    )
    textract_client = session.client("textract")
    return textract_client


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


def process_flight_name(region_name, text, ticket_type=None):
    if not text.isalnum() or len(text) < 4:
        return {region_name: None}
    return {region_name: text.strip()}


def validate_coordinates(image, region_coordinates):
    x, y, w, h = region_coordinates
    height, width = image.shape[:2]

    if x < 0 or y < 0 or x + w > width or y + h > height:
        return False
    return True


def process_text_detection(client, document):
    response = client.analyze_document(
        Document={"Bytes": document}, FeatureTypes=["TABLES", "FORMS"]
    )
    return response


def extract_text_and_confidence(response):
    extracted_data = []
    for block in response["Blocks"]:
        if block["BlockType"] in ["LINE"]:
            extracted_data.append(
                {"Text": block["Text"], "Confidence": block["Confidence"]}
            )
    print("===== Extracted Data =====")
    print(extracted_data)
    return extracted_data


def extract_text(image, region_coordinates, client):
    x, y, w, h = region_coordinates
    region_image = image[y : y + h, x : x + w]

    # Convert the region image to image bytes using an in-memory buffer
    is_success, buffer = cv2.imencode(".png", region_image)
    image_bytes = io.BytesIO(buffer).getvalue()

    # Analyze the document using Textract
    response = process_text_detection(client, image_bytes)

    # Extract the text and confidence values
    extracted_data = extract_text_and_confidence(response)

    # Combine the extracted text into a single string
    text = " ".join([item["Text"] for item in extracted_data])

    return text


def process_text(region_name, text, processing_function, ticket_type=None):
    text = text.strip()
    if not text:
        return {region_name: None}

    if processing_function:
        return processing_function(region_name, text, ticket_type)
    else:
        return {region_name: text.strip()}


def process_document(image, config, textract_client, ticket_type=None):
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
                "process_flight_name": process_flight_name,
            }
            processing_function = processing_functions.get(processing_function_name)

        if validate_coordinates(preprocessed_image, region_coordinates):
            text = extract_text(preprocessed_image, region_coordinates, textract_client)
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


def load_and_process_config(image, textract_client):
    if image is not None:
        config_path = os.path.join(
            os.path.dirname(__file__), "configs", "emirates_ticket_config.json"
        )
        config = load_config(config_path)
        if config is None:
            print(
                "Error loading the configuration file. Please check the file path and format."
            )
            return None
        return process_document(image, config, textract_client)
    else:
        print("Error reading the input image.")
        return None


def extract_ticket_info(file_path):
    textract_client = setup_textract_client(
        access_key=os.getenv("AWS_ACCESS_KEY"), secret_key=os.getenv("AWS_SECRET_KEY")
    )

    file_extension = os.path.splitext(file_path)[1].lower()
    image = read_image(file_path, file_extension)
    extracted_data = load_and_process_config(image, textract_client)
    return extracted_data
