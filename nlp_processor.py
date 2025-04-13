from transformers import pipeline

# Load the pre-trained NLP model locally
def load_local_model():
    return pipeline("text-classification", model="distilbert-base-uncased")

# Initialize the model once (singleton pattern)
nlp = load_local_model()

def interpret_query(query):
    # Define mappings for common scraping tasks
    task_mappings = {
        "product names": ["product", "name", "item"],
        "prices": ["price", "cost", "amount"],
        "headings": ["heading", "title", "header"],
        "text": ["text", "content", "displayed", "visible"],
        "images": ["image", "images", "photo", "photos", "picture", "pictures"]
    }
    
    # Tokenize the query into lowercase words
    tokens = query.lower().split()
    
    # Identify matching tasks
    result = {}
    for task, keywords in task_mappings.items():
        if any(keyword in tokens for keyword in keywords):
            result["task"] = task
            break
    
    # Add filters if specified (e.g., "only headings with 'sale'")
    if "only" in tokens:
        index = tokens.index("only")
        filter_words = tokens[index + 1:]
        result["filter"] = " ".join(filter_words)
    
    return result