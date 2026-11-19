from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_DIR = ROOT / ".codex-build" / "defense-deck"
OUTPUT_PATH = ROOT / "deliverables" / "smart-waste-sorting-defense-final.pdf"
PAGE_SIZE = (1600, 900)
SLIDE_COUNT = 8


def main() -> None:
    slides = [PREVIEW_DIR / f"slide-{number:02}.png" for number in range(1, SLIDE_COUNT + 1)]
    missing = [str(path) for path in slides if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing rendered slide images: " + ", ".join(missing))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix="defense-deck-", suffix=".pdf", dir=PREVIEW_DIR)
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        deck = canvas.Canvas(str(temporary_path), pagesize=PAGE_SIZE, pageCompression=1)
        deck.setTitle("智能垃圾视觉分拣系统 - 招新考核项目说明")
        deck.setAuthor("王吉祥")
        for slide_path in slides:
            deck.drawImage(ImageReader(str(slide_path)), 0, 0, width=PAGE_SIZE[0], height=PAGE_SIZE[1])
            deck.showPage()
        deck.save()
        temporary_path.replace(OUTPUT_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)

    print(json.dumps({"path": str(OUTPUT_PATH), "pages": SLIDE_COUNT, "pageSize": PAGE_SIZE, "bytes": OUTPUT_PATH.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
