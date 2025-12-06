from pdf2image import convert_from_path
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image

def ocr_pdf_to_text(pdf_path, txt_path, lang="rus"):
    poppler_path = r"C:\Program Files\poppler\Library\bin"
    pages = convert_from_path(pdf_path, dpi=150, poppler_path=poppler_path)
    print(f"Получено страниц: {len(pages)}")

    with open(txt_path, "w", encoding="utf-8") as f:
        for i, page in enumerate(pages, start=1):
            print(f"Распознаётся страница {i}/{len(pages)}...")
            text = pytesseract.image_to_string(page, lang=lang)
            f.write(text + "\n\n")
            print(f"Готово: страница {i}")

    print("Распознавание завершено!")

ocr_pdf_to_text("scan.pdf", "result.txt")



