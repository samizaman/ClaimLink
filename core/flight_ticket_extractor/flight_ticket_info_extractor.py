import json
import os
from datetime import datetime

import cv2
import numpy as np
import pytesseract
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


def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray


def validate_coordinates(image, region_coordinates):
    x, y, w, h = region_coordinates
    height, width = image.shape[:2]

    if x < 0 or y < 0 or x + w > width or y + h > height:
        return False
    return True


def extract_text(image, region_coordinates, config):
    x, y, w, h = region_coordinates
    region_image = image[y : y + h, x : x + w]
    text = pytesseract.image_to_string(region_image, config=config)
    return text.strip()


def process_text(region_name, text, processing_function, ticket_type=None):
    text = text.strip()
    if not text:
        return {region_name: None}

    if processing_function:
        return processing_function(region_name, text, ticket_type)
    else:
        return {region_name: text.strip()}


def process_name(region_name, text, ticket_type=None):
    text = text.replace("\n", " ").replace("/", "")
    name_parts = text.split()

    if ticket_type == "emirates":
        if len(name_parts) > 1:
            first_name = name_parts[-1]
            last_name = " ".join(name_parts[:-1])
            salutation = first_name[-2:].upper()
            first_name = first_name[:-2]
        else:
            salutation = ""
            first_name = ""
            last_name = ""
    elif ticket_type == "flynas":
        if len(name_parts) == 3:
            salutation, first_name, last_name = name_parts
        else:
            salutation = ""
            first_name = ""
            last_name = ""
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
    date_formats = ["%d%b%Y", "%A %d %B %Y"]

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


def process_document(image, config, ticket_type=None):
    preprocessed_image = preprocess_image(image)
    extracted_data = {}

    for region_name, region_info in config["regions"].items():
        region_coordinates = region_info["coordinates"]
        ocr_config = region_info["ocr_config"]
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
            text = extract_text(preprocessed_image, region_coordinates, ocr_config)
            processed_data = process_text(
                region_name, text, processing_function, ticket_type
            )
        else:
            print(f"Invalid coordinates for region: {region_name}")
            processed_data = {region_name: None}

        extracted_data.update(processed_data)

    return extracted_data


def extract_ticket_info(file_path):
    extracted_data = None

    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == ".pdf":
        images = convert_pdf_to_images(file_path)
        if images:
            image = images[0]
            # Convert PIL image to OpenCV Mat
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Extract flight_name without any configuration
            flight_name_region_coordinates = (
                0,
                0,
                image.shape[1],
                int(image.shape[0] * 0.2),
            )
            flight_name = extract_text(image, flight_name_region_coordinates, "--psm 6")

            # Choose the appropriate configuration file based on flight_name
            if "Emirates" in flight_name:
                print("===emirates===")
                config_path = "configs/emirates_ticket_config.json"
                ticket_type = "emirates"
            elif "flynas" in flight_name:
                print("===flynas===")
                config_path = "configs/flynas_ticket_config.json"
                ticket_type = "flynas"
            else:
                print("Unknown flight name. Please provide a valid ticket.")
                return

            config = load_config(config_path)
            if config is None:
                print(
                    "Error loading the configuration file. Please check the file path and format."
                )
                return
            extracted_data = process_document(image, config, ticket_type)
            for key, value in extracted_data.items():
                print(f"{key}: {value}")
            print()
        else:
            print("No images found in the PDF.")
    else:
        try:
            # Process the input image directly
            image = cv2.imread(file_path)
        except Exception as e:
            print(f"Error reading the input image: {e}")
            return
        if image is not None:
            # Extract flight_name without any configuration
            flight_name_region_coordinates = (
                0,
                0,
                image.shape[1],
                int(image.shape[0] * 0.1),
            )
            flight_name = extract_text(image, flight_name_region_coordinates, "--psm 6")

            # Choose the appropriate configuration file based on flight_name
            if "Emirates" in flight_name:
                config_path = "configs/emirates_ticket_config.json"
                ticket_type = "emirates"
            elif "flynas" in flight_name:
                config_path = "configs/flynas_ticket_config.json"
                ticket_type = "flynas"
            else:
                print("Unknown flight name. Please provide a valid ticket.")
                return

            config = load_config(config_path)
            if config is None:
                print(
                    "Error loading the configuration file. Please check the file path and format."
                )
                return
            extracted_data = process_document(image, config, ticket_type)
            for key, value in extracted_data.items():
                print(f"{key}: {value}")
        else:
            print("Error reading the input image.")
    return extracted_data
