import re
from typing import Dict

TASK_MAPPINGS = {
    "product names": ["product", "products", "name", "names", "item", "items"],
    "prices": ["price", "prices", "cost", "costs", "amount", "amounts"],
    "headings": ["heading", "headings", "title", "titles", "header", "headers"],
    "text": ["text", "content", "words", "paragraph", "paragraphs", "visible"],
    "images": ["image", "images", "photo", "photos", "picture", "pictures"],
}


def _tokenize(query: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9']+", query.lower())


def interpret_query(query: str) -> Dict[str, str]:
    """Interpret a natural-language scraping query.

    Returns a dictionary with:
    - task: one of supported scraping tasks
    - filter: optional keyword filter text
    """
    tokens = _tokenize(query)

    result: Dict[str, str] = {}
    for task, keywords in TASK_MAPPINGS.items():
        if any(keyword in tokens for keyword in keywords):
            result["task"] = task
            break

    # Parse filter phrases like:
    # - only red
    # - only red shoes
    # - containing sale
    # - with keyword sale
    filter_patterns = [
        r"\bonly\s+(.+)$",
        r"\bcontaining\s+(.+)$",
        r"\bwith\s+(?:keyword\s+)?(.+)$",
    ]

    lowered = query.lower().strip()
    for pattern in filter_patterns:
        match = re.search(pattern, lowered)
        if match:
            filter_text = match.group(1).strip(" .,!?:;\"'")
            if filter_text:
                result["filter"] = filter_text
            break

    return result
