import io
import json

import boto3
import cv2
from botocore.exceptions import ClientError


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
        if block["BlockType"] in ["LINE"]:
            extracted_data.append(
                {"Text": block["Text"], "Confidence": block["Confidence"]}
            )
    print("===== Extracted Data =====")
    print(extracted_data)
    return extracted_data


def extract_text(
    image=None,
    region_coordinates=None,
    textract_client=None,
    image_path=None,
    use_aws=True,
):
    if not use_aws:
        print("AWS API usage is disabled.")
        return ""

    if image_path:
        # Read the image
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
    elif image is not None:
        if region_coordinates:
            x, y, w, h = region_coordinates
            region_image = image[y : y + h, x : x + w]
            # Convert the region image to image bytes using an in-memory buffer
            is_success, buffer = cv2.imencode(".png", region_image)
            image_bytes = io.BytesIO(buffer).getvalue()
        else:
            is_success, buffer = cv2.imencode(".png", image)
            image_bytes = io.BytesIO(buffer).getvalue()
    else:
        raise ValueError("Either image or image_path must be provided.")

    # Analyze the document using Textract
    response = process_text_detection(textract_client, image_bytes)

    # Extract the text and confidence values
    extracted_data = extract_text_and_confidence(response)

    # Combine the extracted text into a single string
    text = " ".join([item["Text"] for item in extracted_data])

    return text


def load_config(config_path):
    try:
        with open(config_path, "r") as config_file:
            config_data = json.load(config_file)
        return config_data
    except Exception as e:
        print(f"Error loading configuration file: {e}")
        return None
