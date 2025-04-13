from scraper import scrape_website
from nlp_processor import interpret_query
import os

def main():
    print("Welcome to the AI-Powered Web Scraper!")
    
    # Get user inputs
    url = input("Enter the website URL: ").strip()
    query = input("What do you want to scrape? ").strip()
    
    if not url or not query:
        print("Please provide both a valid URL and a query.")
        return
    
    # Interpret the query using NLP
    elements = interpret_query(query)
    if not elements:
        print("Sorry, I couldn't understand your query. Please try again.")
        return
    
    # Scrape the website
    print(f"Scraping {url} for {', '.join(elements)}...")
    try:
        # Ensure the output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Perform the scraping
        data = scrape_website(url, elements)
        
        # Save the output to a file
        output_file = "output/output.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            for key, values in data.items():
                file.write(f"{key.capitalize()}:\n")
                for value in values:
                    file.write(f"- {value}\n")
                file.write("\n")
        
        print(f"Scraping completed! Check the '{output_file}' file for results.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()