from bs4 import BeautifulSoup
import requests
from playwright.sync_api import sync_playwright
import os
from urllib.parse import urljoin, urlparse

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


def fetch_static_website(url):
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def fetch_dynamic_website(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()
    return html


def get_final_image_url(image_url):
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"}:
        return image_url

    try:
        response = requests.get(image_url, headers=REQUEST_HEADERS, timeout=15, stream=True, allow_redirects=True)
        response.close()
        return response.url
    except Exception as e:
        print(f"Failed to resolve image URL: {image_url}. Error: {e}")
        return image_url


def _extract_readable_text(soup):
    content_root = soup.find("article") or soup.find("main") or soup.body or soup

    for tag in content_root.find_all(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()

    text_tags = content_root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "th", "td"])

    cleaned = []
    seen = set()
    for tag in text_tags:
        text = " ".join(tag.get_text(" ", strip=True).split())
        if not text:
            continue

        # Keep content-like lines, skip tiny/label-like fragments.
        words = text.split()
        if len(words) < 4 and len(text) < 28:
            continue

        lowered = text.lower()
        if lowered in seen:
            continue

        seen.add(lowered)
        cleaned.append(text)

    return cleaned


def extract_data(html, task, filter_text=None, url=None):
    soup = BeautifulSoup(html, "html.parser")
    result = []

    if task == "product names":
        tags = soup.find_all(["h1", "span"], class_=lambda x: x and "name" in x)
        result = [tag.text.strip() for tag in tags]
    elif task == "prices":
        tags = soup.find_all(["span", "div"], class_=lambda x: x and "price" in x)
        result = [tag.text.strip() for tag in tags]
    elif task == "headings":
        tags = soup.find_all(["h1", "h2", "h3"])
        result = [tag.text.strip() for tag in tags]
    elif task == "text":
        result = _extract_readable_text(soup)
    elif task == "images":
        img_tags = soup.find_all("img")
        result = []
        for img in img_tags:
            src = img.get("src") or img.get("data-src")
            if src and src.strip():
                absolute_url = urljoin(url, src)
                final_url = get_final_image_url(absolute_url)
                result.append(final_url)

    if filter_text:
        result = [item for item in result if filter_text.lower() in item.lower()]

    return result


def download_images(img_urls, output_dir="output/images"):
    os.makedirs(output_dir, exist_ok=True)

    for i, img_url in enumerate(img_urls):
        try:
            parsed = urlparse(img_url)
            if parsed.scheme not in {"http", "https"}:
                print(f"Skipping unsupported image URL: {img_url}")
                continue

            print(f"Attempting to download: {img_url}")
            response = requests.get(img_url, headers=REQUEST_HEADERS, timeout=20)
            if response.status_code == 200:
                ext = img_url.split(".")[-1].split("?")[0]
                if ext.lower() not in ["jpg", "jpeg", "png", "gif", "webp"]:
                    ext = "jpg"
                img_path = os.path.join(output_dir, f"image_{i}.{ext}")
                with open(img_path, "wb") as img_file:
                    img_file.write(response.content)
                print(f"Downloaded: {img_path}")
            else:
                print(f"Failed to download {img_url}: Status code {response.status_code}")
        except Exception as e:
            print(f"Failed to download {img_url}: {e}")


def scrape_website(url, task, filter_text=None):
    try:
        html = fetch_static_website(url)
    except Exception as static_error:
        try:
            html = fetch_dynamic_website(url)
        except Exception as dynamic_error:
            raise Exception(
                f"Unable to fetch website content. Static error: {static_error}. Dynamic error: {dynamic_error}"
            )

    data = extract_data(html, task, filter_text, url)

    if task == "images":
        download_images(data)

    return data
