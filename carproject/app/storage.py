from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

BASE_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "ocr"
BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_ocr_text(source_filename: str, text: str) -> Dict[str, str]:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    stem = Path(source_filename).stem or "document"
    text_path = BASE_DATA_DIR / f"{stem}_{timestamp}.txt"
    text_path.write_text(text, encoding="utf-8")
    return {
        "path": str(text_path),
        "timestamp": timestamp,
        "original_filename": source_filename,
    }
