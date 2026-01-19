import boto3
import fitz  # PyMuPDF
import json
import os
import time


# Configuration
INPUT_PDF = "input/bylaws.pdf"
CACHE_DIR = "ocr_cache"
AWS_REGION = "us-east-2"
DPI = 350
SLEEP_SECONDS = 0.15

os.makedirs(CACHE_DIR, exist_ok=True)

textract = boto3.client("textract", region_name=AWS_REGION)

def ocr_page(image_bytes):
    """
    Send a single page image to AWS Textract
    and return the full JSON response.
    """
    return textract.detect_document_text(
        Document={"Bytes": image_bytes}
    )


def main():
    doc = fitz.open(INPUT_PDF)
    total_pages = len(doc)

    print(f"Starting Textract OCR for {total_pages} pages")

    for page_index in range(total_pages):
        page_number = page_index + 1
        cache_path = f"{CACHE_DIR}/page_{page_number:03}.json"

        # Skip pages already processed
        if os.path.exists(cache_path):
            print(f"✓ Page {page_number} already cached — skipping")
            continue

        print(f"→ OCR Page {page_number}/{total_pages}")

        page = doc.load_page(page_index)

        # Render page as a high-resolution image
        pix = page.get_pixmap(dpi=DPI)
        image_bytes = pix.tobytes("png")

        try:
            response = ocr_page(image_bytes)

            # Save raw Textract output
            with open(cache_path, "w") as f:
                json.dump(response, f, indent=2)

            # Prevent API throttling
            time.sleep(SLEEP_SECONDS)

        except Exception as e:
            print(f"⚠️ Failed page {page_number}: {e}")

    print("✅ Textract OCR complete")

if __name__ == "__main__":
    main()
