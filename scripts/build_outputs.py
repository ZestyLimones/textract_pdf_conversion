import fitz
import json
import os

INPUT_PDF = "input/bylaws.pdf"
CACHE_DIR = "ocr_cache"
OUTPUT_DIR = "output"

OUTPUT_PDF = f"{OUTPUT_DIR}/bylaws_searchable.pdf"
OUTPUT_MD = f"{OUTPUT_DIR}/bylaws.md"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_lines(textract_json):
    """
    Pull only LINE-level text from Textract output.
    """
    return [
        block["Text"]
        for block in textract_json["Blocks"]
        if block["BlockType"] == "LINE"
    ]

def main():
    source_doc = fitz.open(INPUT_PDF)
    output_doc = fitz.open()
    markdown_pages = []

    total_pages = len(source_doc)

    for page_index in range(total_pages):
        page_number = page_index + 1
        cache_path = f"{CACHE_DIR}/page_{page_number:03}.json"

        print(f"Building page {page_number}/{total_pages}")

        if not os.path.exists(cache_path):
            print(f"⚠️ Missing OCR data for page {page_number}")
            continue

        with open(cache_path) as f:
            textract_data = json.load(f)

        lines = extract_lines(textract_data)
        page_text = "\n".join(lines)

        # ---------- Markdown ----------
        markdown_pages.append(f"## Page {page_number}\n")
        markdown_pages.append(page_text + "\n")

        # ---------- Searchable PDF ----------
        page = source_doc.load_page(page_index)
        pix = page.get_pixmap(dpi=350)
        image_bytes = pix.tobytes("png")

        new_page = output_doc.new_page(
            width=page.rect.width,
            height=page.rect.height
        )

        # Original scanned image
        new_page.insert_image(page.rect, stream=image_bytes)

        # Invisible text layer
        writer = fitz.TextWriter(new_page.rect)
        y = 30

        for line in lines:
            writer.append(
                fitz.Point(30, y),
                line,
                fontsize=8
            )
            y += 11

        writer.write_text(new_page, render_mode=3)

    output_doc.save(OUTPUT_PDF)
    output_doc.close()

    with open(OUTPUT_MD, "w") as f:
        f.write("\n".join(markdown_pages))

    print("✅ Outputs generated")

if __name__ == "__main__":
    main()
