import json
import os
import re

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from PIL import Image
from pyzbar.pyzbar import decode

load_dotenv()


def load_airline_configs(file_path):
    with open(file_path, "r") as file:
        configs = json.load(file)
    return configs


AIRLINE_CONFIGS = load_airline_configs(
    os.path.join(os.path.dirname(__file__), "configs", "airline_configs.json")
)


def setup_textract_client(access_key, secret_key):
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-west-2",
    )
    textract_client = session.client("textract")
    return textract_client


def process_text_detection(client, document):
    try:
        response = client.analyze_document(
            Document={"Bytes": document}, FeatureTypes=["TABLES", "FORMS"]
        )
    except ClientError:
        print("Couldn't detect text.")
        raise
    else:
        return response


def extract_text_and_confidence(response):
    extracted_data = []
    for block in response["Blocks"]:
        if block["BlockType"] in ["LINE", "WORD"]:
            extracted_data.append(
                {"Text": block["Text"], "Confidence": block["Confidence"]}
            )
    return extracted_data


def extract_text(image_path, textract_client):
    # Read the image
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    # Analyze the document using Textract
    response = process_text_detection(textract_client, image_bytes)

    # Extract the text and confidence values
    extracted_data = extract_text_and_confidence(response)

    # Combine the extracted text into a single string
    text = " ".join([item["Text"] for item in extracted_data])

    return text


def read_barcode(image_path):
    image = Image.open(image_path)
    barcodes = decode(image)

    if barcodes:
        return barcodes[0].data.decode("utf-8")
    else:
        return None


def extract_details(text, airline_config):
    # Extract airline name
    airline_name_match = re.search(
        airline_config["airline_name_regex"], text, re.IGNORECASE
    )
    airline_name = airline_name_match.group(0) if airline_name_match else None

    # Extract flight number
    flight_number_match = re.search(airline_config["flight_number_regex"], text)
    flight_number = flight_number_match.group(0) if flight_number_match else None

    # Extract booking reference number
    booking_ref_match = re.search(airline_config["booking_ref_regex"], text)
    booking_ref = booking_ref_match.group(0) if booking_ref_match else None

    # Extract passenger name
    passenger_name_match = re.search(airline_config["passenger_name_regex"], text)
    passenger_name = passenger_name_match.group(0) if passenger_name_match else None

    return airline_name, flight_number, booking_ref, passenger_name


def process_baggage_tag(image_path, textract_client):
    text = extract_text(image_path, textract_client)
    if text is None:
        print("Failed to extract text.")
        return None

    barcode = read_barcode(image_path)
    if barcode is None:
        print("Failed to read barcode.")
        return None

    # Determine the airline based on the extracted text
    airline = None
    for airline_key in AIRLINE_CONFIGS:
        if re.search(
            AIRLINE_CONFIGS[airline_key]["airline_name_regex"], text, re.IGNORECASE
        ):
            airline = airline_key
            break

    if airline is None:
        print("Airline not found.")
        return None

    airline_config = AIRLINE_CONFIGS[airline]
    airline_name, flight_number, booking_ref, passenger_name = extract_details(
        text, airline_config
    )

    return {
        "airline_name": airline_name,
        "flight_number": flight_number,
        "booking_ref": booking_ref,
        "passenger_name": passenger_name,
        "barcode": barcode,
        "extracted_text": text,
    }


def process_baggage_tag_image(image_path):
    textract_client = setup_textract_client(
        access_key=os.getenv("AWS_ACCESS_KEY"), secret_key=os.getenv("AWS_SECRET_KEY")
    )
    result = process_baggage_tag(image_path, textract_client)
    return result
