from flask import Flask, render_template, request, send_file
import os
from scraper import scrape_website
from nlp_processor import interpret_query

app = Flask(__name__)

# Ensure output directories exist
os.makedirs("output", exist_ok=True)
os.makedirs("output/images", exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url").strip()
        query = request.form.get("query").strip()

        if not url or not query:
            return render_template("index.html", error="Please provide both a URL and a query.")

        # Interpret the query
        parsed_query = interpret_query(query)
        if not parsed_query.get("task"):
            return render_template("index.html", error="Sorry, I couldn't understand your query. Please try again.")

        task = parsed_query["task"]
        filter_text = parsed_query.get("filter")

        # Scrape the website
        try:
            data = scrape_website(url, task, filter_text)
            
            # Save text output to a file
            output_file = "output/output.txt"
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(f"{task.capitalize()}:\n")
                for item in data:
                    file.write(f"- {item}\n")
                file.write("\n")

            # Prepare response
            result = {
                "text": f"Scraping completed! Found {len(data)} items.",
                "data": data,
                "download_link": "/download"
            }
            return render_template("index.html", result=result)
        except Exception as e:
            return render_template("index.html", error=f"An error occurred: {e}")

    return render_template("index.html")

@app.route("/download")
def download():
    return send_file("output/output.txt", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)