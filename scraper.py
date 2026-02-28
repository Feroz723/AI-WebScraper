from bs4 import BeautifulSoup
import requests
from playwright.sync_api import sync_playwright
import os
from urllib.parse import urljoin


def fetch_static_website(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page: {response.status_code}")
    return response.text


def fetch_dynamic_website(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()
    return html


def get_final_image_url(image_url):
    try:
        response = requests.head(image_url, allow_redirects=True)
        return response.url
    except Exception as e:
        print(f"Failed to resolve image URL: {image_url}. Error: {e}")
        return image_url


def _extract_readable_text(soup):
    content_root = soup.find("article") or soup.find("main") or soup.body or soup
    text_tags = content_root.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "th", "td"]
    )

    cleaned = []
    seen = set()
    for tag in text_tags:
        text = " ".join(tag.get_text(" ", strip=True).split())
        if not text or len(text) < 2:
            continue
        if text in seen:
            continue
        seen.add(text)
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
            print(f"Attempting to download: {img_url}")
            response = requests.get(img_url)
            if response.status_code == 200:
                ext = img_url.split(".")[-1].split("?")[0]
                if ext.lower() not in ["jpg", "jpeg", "png", "gif"]:
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
    except Exception:
        html = fetch_dynamic_website(url)

    data = extract_data(html, task, filter_text, url)

    if task == "images":
        download_images(data)

    return data
