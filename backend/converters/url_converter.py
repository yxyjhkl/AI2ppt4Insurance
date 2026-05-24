"""URL/HTML to Markdown converter."""
import re
import ipaddress
from urllib.parse import urlparse
from markdownify import markdownify as md
from bs4 import BeautifulSoup
import requests


def _validate_url(url: str) -> None:
    """Validate that a URL is safe to fetch. Blocks internal/private IPs and non-HTTP schemes."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}. Only http/https are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no valid hostname")

    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            raise ValueError(f"Access to localhost is not allowed: {hostname}")
        return

    if addr.is_loopback or addr.is_private or addr.is_link_local or addr.is_multicast or addr.is_unspecified:
        raise ValueError(f"Access to internal/private IP addresses is not allowed: {hostname}")


def url_to_markdown(url: str) -> str:
    _validate_url(url)
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
