import os

# Set Playwright browser path to project directory
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playwright_browsers")

from scraper import scrape_website
from nlp_processor import interpret_query


def main():
    print("Welcome to the AI-Powered Web Scraper!")

    url = input("Enter the website URL: ").strip()
    query = input("What do you want to scrape? ").strip()

    if not url or not query:
        print("Please provide both a valid URL and a query.")
        return

    parsed_query = interpret_query(query)
    task = parsed_query.get("task")
    filter_text = parsed_query.get("filter")

    if not task:
        print("Sorry, I couldn't understand your query. Please try again.")
        return

    print(f"Scraping {url} for {task}...")
    try:
        os.makedirs("output", exist_ok=True)

        data = scrape_website(url, task, filter_text)

        output_file = "output/output.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(f"{task.capitalize()}:\n")
            for value in data:
                file.write(f"- {value}\n")
            file.write("\n")

        print(f"Scraping completed! Check the '{output_file}' file for results.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
