from pathlib import Path
from typing import Dict, Any

import easyocr
import numpy as np
import pypdfium2 as pdfium
from PIL import Image

_READER = None

def get_reader() -> easyocr.Reader:
    global _READER
    if _READER is None:
        _READER = easyocr.Reader(["en"], gpu=False)
    return _READER

def _image_to_text_array(img: Image.Image):
    reader = get_reader()
    arr = np.array(img)
    lines = reader.readtext(arr, detail=0, paragraph=True)
    return lines

def ocr_image_file(path: str) -> Dict[str, Any]:
    p = Path(path)
    reader = get_reader()
    lines = reader.readtext(str(p), detail=0, paragraph=True)
    full_text = "\n".join(l.strip() for l in lines if l and l.strip())
    return {"pages": [{"number": 1, "text": full_text}], "full_text": full_text}

def ocr_pdf_file(path: str) -> Dict[str, Any]:
    pdf = pdfium.PdfDocument(path)
    pages = []
    for index in range(len(pdf)):
        page = pdf.get_page(index)
        bitmap = page.render(scale=2.0)  # increase DPI for better OCR
        pil_image = bitmap.to_pil()
        lines = _image_to_text_array(pil_image)
        page_text = "\n".join(l.strip() for l in lines if l and l.strip())
        pages.append({"number": index + 1, "text": page_text})
        bitmap.close()
        page.close()
    pdf.close()
    full_text = "\n\n".join(p["text"] for p in pages)
    return {"pages": pages, "full_text": full_text}

def ocr_file(path: str) -> Dict[str, Any]:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        return ocr_pdf_file(str(p))
    return ocr_image_file(str(p))
