from flask import Flask, render_template, request, send_file, Response, jsonify
import os
import json
import time

# Set Playwright browser path to project directory
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playwright_browsers")

from io import BytesIO
from urllib.parse import urlparse
import requests as http_requests
from scraper import fetch_static_website, fetch_dynamic_website, extract_data, download_images
from nlp_processor import interpret_query

app = Flask(__name__)

# Ensure output directories exist
os.makedirs("output", exist_ok=True)
os.makedirs("output/images", exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scrape")
def scrape():
    """SSE endpoint that streams progress events during scraping."""
    url = request.args.get("url", "").strip()
    query = request.args.get("query", "").strip()

    def generate():
        def send_event(progress, message, data=None, error=None, task=None):
            event = {"progress": progress, "message": message}
            if data is not None:
                event["data"] = data
            if error is not None:
                event["error"] = error
            if task is not None:
                event["task"] = task
            return f"data: {json.dumps(event)}\n\n"

        # Validate inputs
        if not url or not query:
            yield send_event(0, "Error", error="Please provide both a URL and a query.")
            return

        # Stage 1: Interpret query (10%)
        yield send_event(10, "Analyzing your query...")
        parsed_query = interpret_query(query)
        task = parsed_query.get("task", "text")
        filter_text = parsed_query.get("filter")
        time.sleep(0.3)  # Small delay so progress is visible

        # Stage 2: Fetch page (40%)
        yield send_event(40, f"Fetching page content...")
        try:
            try:
                html = fetch_static_website(url)
            except Exception:
                html = fetch_dynamic_website(url)
        except Exception as e:
            yield send_event(0, "Error", error=f"Failed to fetch page: {e}")
            return

        # Stage 3: Extract data (70%)
        yield send_event(70, f"Extracting {task}...")
        try:
            data = extract_data(html, task, filter_text, url)
        except Exception as e:
            yield send_event(0, "Error", error=f"Failed to extract data: {e}")
            return

        # Stage 4: Save results (90%)
        yield send_event(90, "Saving results...")
        try:
            output_file = "output/output.txt"
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(f"{task.capitalize()}:\n")
                for item in data:
                    file.write(f"- {item}\n")
                file.write("\n")

            if task == "images":
                download_images(data)
        except Exception as e:
            yield send_event(0, "Error", error=f"Failed to save results: {e}")
            return

        # Stage 5: Complete (100%)
        yield send_event(100, f"Done! Found {len(data)} items.", data=data, task=task)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/download")
def download():
    return send_file("output/output.txt", as_attachment=True)


@app.route("/download-image")
def download_image():
    image_url = request.args.get("url", "").strip()
    if not image_url:
        return "Missing image URL", 400

    try:
        response = http_requests.get(image_url, timeout=20)
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
