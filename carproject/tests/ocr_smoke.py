from pathlib import Path
from PIL import Image, ImageDraw

from app.ocr_service import ocr_image_file


def run_smoke_test() -> None:
    img_path = Path("app/uploads/_ocr_smoke.png")
    img_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (300, 120), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "Test Lease", fill="black")
    img.save(img_path)

    result = ocr_image_file(str(img_path))
    print("OCR text:", result["full_text"].strip())


if __name__ == "__main__":
    run_smoke_test()
