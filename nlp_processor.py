import re
import math
from typing import Dict
from difflib import SequenceMatcher
from collections import Counter

# --- AI-Powered Query Understanding (Pure Python, No External Dependencies) ---
# Uses TF-IDF-like word overlap + fuzzy matching to understand any query phrasing.
# Fully offline, instant loading, zero dependencies.

# Training examples: diverse phrasings mapped to each task
TRAINING_DATA = [
    # Links
    ("extract all hyperlinks and urls from the page", "links"),
    ("get all backlinks and anchor links", "links"),
    ("find all website references and external links", "links"),
    ("scrape all href attributes from anchor tags", "links"),
    ("show me all the links on this page", "links"),
    ("grab all outbound and inbound links", "links"),
    ("get all urls", "links"),
    ("scape all the available backlinks", "links"),
    ("find references", "links"),
    ("list all anchors", "links"),
    ("external links on this page", "links"),
    ("internal navigation links", "links"),
    ("all clickable links", "links"),
    ("hyperlinks present on this website", "links"),
    ("get the href values", "links"),
    ("fetch all the redirects", "links"),

    # Images
    ("extract all images and photos from the page", "images"),
    ("download all pictures and thumbnails", "images"),
    ("get all image sources and photo urls", "images"),
    ("scrape all img tags and their src attributes", "images"),
    ("find all visual media on this page", "images"),
    ("show me the pictures", "images"),
    ("get photos", "images"),
    ("image gallery", "images"),
    ("all pics on this site", "images"),
    ("download graphics", "images"),
    ("find logos and icons", "images"),
    ("banner images", "images"),
    ("get the screenshots", "images"),
    ("photo collection from this page", "images"),

    # Product names
    ("extract all product names and item titles", "product names"),
    ("get all product listings and merchandise names", "product names"),
    ("find the names of all products on this page", "product names"),
    ("scrape product titles and item descriptions", "product names"),
    ("list all items for sale", "product names"),
    ("what products are available", "product names"),
    ("show me available merchandise", "product names"),
    ("product catalog listing", "product names"),
    ("items being sold", "product names"),
    ("all item names", "product names"),
    ("product inventory", "product names"),

    # Prices
    ("extract all prices and costs from the page", "prices"),
    ("get all product prices and amounts", "prices"),
    ("find the pricing information and rates", "prices"),
    ("scrape all monetary values and price tags", "prices"),
    ("how much does it cost", "prices"),
    ("show me the rates", "prices"),
    ("what are the charges", "prices"),
    ("discount and offers pricing", "prices"),
    ("all amount and tariff details", "prices"),
    ("cost of each item", "prices"),
    ("price list", "prices"),

    # Headings
    ("extract all headings and titles from the page", "headings"),
    ("get all h1 h2 h3 headers and section titles", "headings"),
    ("find all heading elements and subheadings", "headings"),
    ("scrape the page structure and heading hierarchy", "headings"),
    ("table of contents structure", "headings"),
    ("main headlines on this page", "headings"),
    ("section headers", "headings"),
    ("page outline and structure", "headings"),
    ("all subtitles", "headings"),

    # Text (also the fallback for general/vague queries)
    ("extract all text content from the page", "text"),
    ("get all visible text and paragraphs", "text"),
    ("scrape the full page content and body text", "text"),
    ("grab everything on this page", "text"),
    ("fetch all the data from this website", "text"),
    ("get all information from this page", "text"),
    ("read the entire page", "text"),
    ("copy all content", "text"),
    ("what does this page say", "text"),
    ("full page dump", "text"),
    ("get me all the data", "text"),
    ("scrape everything", "text"),
    ("extract all details", "text"),
    ("give me all text", "text"),
    ("page content", "text"),
]

# Common stop words to ignore during matching
STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "at", "by", "from", "with", "as", "into", "about", "between",
    "through", "during", "before", "after", "above", "below", "up", "down",
    "out", "off", "over", "under", "again", "further", "then", "once",
    "i", "me", "my", "we", "our", "you", "your", "it", "its", "this",
    "that", "these", "those", "am", "not", "no", "nor", "so", "too",
    "very", "just", "also", "and", "but", "or", "if", "while",
}


def _tokenize(text: str) -> list:
    """Tokenize and clean text."""
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]


def _compute_idf(documents: list) -> dict:
    """Compute inverse document frequency for all terms."""
    doc_count = len(documents)
    df = Counter()
    for doc_tokens in documents:
        unique_tokens = set(doc_tokens)
        for token in unique_tokens:
            df[token] += 1
    return {term: math.log(doc_count / (1 + freq)) for term, freq in df.items()}


# Pre-process training data
_tokenized_docs = [_tokenize(desc) for desc, _ in TRAINING_DATA]
_labels = [label for _, label in TRAINING_DATA]
_idf = _compute_idf(_tokenized_docs)


def _tfidf_vector(tokens: list) -> dict:
    """Create a TF-IDF weighted vector from tokens."""
    tf = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {term: (count / total) * _idf.get(term, 1.0) for term, count in tf.items()}


def _cosine_sim(vec1: dict, vec2: dict) -> float:
    """Compute cosine similarity between two sparse vectors."""
    common_keys = set(vec1.keys()) & set(vec2.keys())
    if not common_keys:
        return 0.0
    dot = sum(vec1[k] * vec2[k] for k in common_keys)
    mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def _fuzzy_bonus(query: str, description: str) -> float:
    """Additional fuzzy matching score to catch typos and close matches."""
    return SequenceMatcher(None, query.lower(), description.lower()).ratio() * 0.3


# Pre-compute TF-IDF vectors for all training descriptions
_doc_vectors = [_tfidf_vector(tokens) for tokens in _tokenized_docs]


def interpret_query(query: str) -> Dict[str, str]:
    """Interpret a natural-language scraping query using AI-powered similarity.

    Uses TF-IDF vectorization + cosine similarity + fuzzy matching to understand
    any query, regardless of how it's phrased.

    Returns a dictionary with:
    - task: one of the supported scraping tasks
    - filter: optional keyword filter text
    """
    result: Dict[str, str] = {}

    # Tokenize and vectorize the query
    query_tokens = _tokenize(query)
    query_vec = _tfidf_vector(query_tokens)

    # Score each training example: TF-IDF cosine similarity + fuzzy bonus
    best_score = -1
    best_task = "text"  # Default fallback

    for idx, doc_vec in enumerate(_doc_vectors):
        tfidf_score = _cosine_sim(query_vec, doc_vec)
        fuzzy_score = _fuzzy_bonus(query, TRAINING_DATA[idx][0])
        combined = tfidf_score + fuzzy_score

        if combined > best_score:
            best_score = combined
            best_task = _labels[idx]

    result["task"] = best_task

    # Parse filter phrases like:
    # - only red
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
