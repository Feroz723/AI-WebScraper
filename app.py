from flask import Flask, render_template, request, send_file
import os
from io import BytesIO
from urllib.parse import urlparse
import requests
from scraper import scrape_website
from nlp_processor import interpret_query

app = Flask(__name__)

# Ensure output directories exist
os.makedirs("output", exist_ok=True)
os.makedirs("output/images", exist_ok=True)


def _escape_pdf_text(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_text_pdf(lines):
    max_lines_per_page = 45
    pages = []
    for start in range(0, max(1, len(lines)), max_lines_per_page):
        pages.append(lines[start : start + max_lines_per_page] or ["No text content found."])

    objects = []

    def add_object(content):
        objects.append(content)
        return len(objects)

    font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids = []
    content_ids = []

    for page_lines in pages:
        y = 790
        text_rows = ["BT", "/F1 11 Tf", "50 790 Td"]
        for idx, line in enumerate(page_lines):
            clean_line = _escape_pdf_text(line)
            if idx == 0:
                text_rows.append(f"({clean_line}) Tj")
            else:
                y -= 16
                text_rows.append(f"50 {y} Td")
                text_rows.append(f"({clean_line}) Tj")
        text_rows.append("ET")
        stream = "\n".join(text_rows)
        content_id = add_object(f"<< /Length {len(stream.encode('latin-1', errors='replace'))} >>\nstream\n{stream}\nendstream")
        content_ids.append(content_id)

        page_id = add_object("PENDING_PAGE")
        page_ids.append(page_id)

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    pages_id = add_object(f"<< /Type /Pages /Kids [ {kids} ] /Count {len(page_ids)} >>")

    for i, page_id in enumerate(page_ids):
        objects[page_id - 1] = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_ids[i]} 0 R >>"
        )

    catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")

    pdf = ["%PDF-1.4\n"]
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part.encode('latin-1', errors='replace')) for part in pdf))
        pdf.append(f"{i} 0 obj\n{obj}\nendobj\n")

    xref_offset = sum(len(part.encode('latin-1', errors='replace')) for part in pdf)
    pdf.append(f"xref\n0 {len(objects) + 1}\n")
    pdf.append("0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.append(f"{off:010d} 00000 n \n")

    pdf.append(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    )

    return "".join(pdf).encode("latin-1", errors="replace")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        query = request.form.get("query", "").strip()

        if not url or not query:
            return render_template("index.html", error="Please provide both a URL and a query.")

        parsed_query = interpret_query(query)
        if not parsed_query.get("task"):
            return render_template("index.html", error="Sorry, I couldn't understand your query. Please try again.")

        task = parsed_query["task"]
        filter_text = parsed_query.get("filter")

        try:
            data = scrape_website(url, task, filter_text)

            output_file = "output/output.txt"
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(f"{task.capitalize()}:\n")
                for item in data:
                    file.write(f"- {item}\n")
                file.write("\n")

            if task == "text":
                pdf_bytes = _build_text_pdf(data)
                with open("output/output.pdf", "wb") as pdf_file:
                    pdf_file.write(pdf_bytes)

            result = {
                "task": task,
                "text": f"Scraping completed! Found {len(data)} items.",
                "data": data,
                "download_link": "/download",
                "text_pdf_link": "/download-pdf" if task == "text" else None,
            }
            return render_template("index.html", result=result)
        except Exception as e:
            return render_template("index.html", error=f"An error occurred: {e}")

    return render_template("index.html")


@app.route("/download")
def download():
    return send_file("output/output.txt", as_attachment=True)


@app.route("/download-pdf")
def download_pdf():
    return send_file("output/output.pdf", as_attachment=True)


@app.route("/preview-pdf")
def preview_pdf():
    return send_file("output/output.pdf", mimetype="application/pdf")


@app.route("/download-image")
def download_image():
    image_url = request.args.get("url", "").strip()
    if not image_url:
        return "Missing image URL", 400

    try:
        response = requests.get(image_url, timeout=20)
        response.raise_for_status()

        parsed = urlparse(image_url)
        filename = os.path.basename(parsed.path) or "scraped_image.jpg"
        if "." not in filename:
            filename += ".jpg"

        content_type = response.headers.get("Content-Type", "image/jpeg")
        return send_file(
            BytesIO(response.content),
            mimetype=content_type,
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return f"Failed to download image: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)
