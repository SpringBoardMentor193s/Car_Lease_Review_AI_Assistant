import os
import requests

def ocr_space_image(file_path: str) -> str:
    api_key = os.getenv("OCR_API_KEY")
    with open(file_path, "rb") as f:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={file_path: f},
            data={"apikey": api_key, "language": "eng"}
        )
    result = response.json()
    if result.get("ParsedResults"):
        return result["ParsedResults"][0]["ParsedText"]
    return ""