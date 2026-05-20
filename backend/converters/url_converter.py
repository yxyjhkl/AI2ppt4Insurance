"""URL/HTML to Markdown converter."""
import re
from markdownify import markdownify as md
from bs4 import BeautifulSoup
import requests


def url_to_markdown(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    try:
        return html_to_markdown(resp.text, url)
    finally:
        resp.close()


def html_to_markdown(html_content: str, base_url: str = "") -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup.find("body")
    if article is None:
        article = soup

    markdown = md(str(article), heading_style="ATX", strip=["a", "img"])

    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = markdown.strip()

    return markdown
