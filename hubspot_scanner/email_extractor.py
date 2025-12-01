"""Email extraction and filtering functionality."""

import re
from typing import Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# Generic email prefixes to exclude
GENERIC_EMAIL_PREFIXES = frozenset([
    "info",
    "support",
    "admin",
    "hello",
    "sales",
    "contact",
    "help",
    "noreply",
    "no-reply",
    "webmaster",
    "postmaster",
    "mail",
    "email",
    "enquiries",
    "enquiry",
    "office",
    "team",
    "general",
])

# Email regex pattern
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
)

# Common pages that might contain contact information
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
    "/team",
    "/our-team",
    "/leadership",
    "/people",
    "/staff",
]


def is_generic_email(email: str) -> bool:
    """
    Check if an email is generic (should be excluded).

    Args:
        email: Email address to check

    Returns:
        True if the email is generic, False otherwise
    """
    local_part = email.split("@")[0].lower()
    return local_part in GENERIC_EMAIL_PREFIXES


def is_valid_email(email: str, domain: str) -> bool:
    """
    Check if an email is valid and relevant.

    Args:
        email: Email address to check
        domain: The domain being scanned

    Returns:
        True if the email is valid and relevant
    """
    email_lower = email.lower()

    # Skip generic emails
    if is_generic_email(email_lower):
        return False

    # Skip obviously fake or example emails
    invalid_domains = ["example.com", "example.org", "test.com", "domain.com"]
    email_domain = email_lower.split("@")[1] if "@" in email_lower else ""
    if email_domain in invalid_domains:
        return False

    # Skip image and file extensions mistakenly captured
    if email_domain.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js")):
        return False

    return True


def extract_emails_from_html(html_content: str, domain: str) -> Set[str]:
    """
    Extract non-generic emails from HTML content.

    Args:
        html_content: The HTML content to parse
        domain: The domain being scanned

    Returns:
        Set of non-generic email addresses
    """
    emails = set()

    # Find all email patterns
    found_emails = EMAIL_PATTERN.findall(html_content)

    for email in found_emails:
        if is_valid_email(email, domain):
            emails.add(email.lower())

    # Also look for mailto: links
    soup = BeautifulSoup(html_content, "lxml")
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0].strip()
            if email and is_valid_email(email, domain):
                emails.add(email.lower())

    return emails


def get_internal_links(html_content: str, base_url: str, domain: str) -> Set[str]:
    """
    Extract internal links from HTML content.

    Args:
        html_content: The HTML content to parse
        base_url: The base URL for resolving relative links
        domain: The domain being scanned

    Returns:
        Set of internal URLs
    """
    soup = BeautifulSoup(html_content, "lxml")
    links = set()
    parsed_base = urlparse(base_url)

    for link in soup.find_all("a", href=True):
        href = link.get("href", "").strip()

        # Skip empty, javascript, and anchor links
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)

        # Only keep internal links
        if parsed_url.netloc == parsed_base.netloc or parsed_url.netloc == domain:
            # Normalize the URL
            normalized = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            links.add(normalized)

    return links


def crawl_for_emails(
    base_url: str,
    domain: str,
    initial_html: str,
    timeout: int = 10,
    user_agent: str = None,
    max_pages: int = 10,
) -> Set[str]:
    """
    Crawl a site to find non-generic email addresses.

    Args:
        base_url: The base URL to start crawling from
        domain: The domain being scanned
        initial_html: The HTML content of the homepage
        timeout: Request timeout in seconds
        user_agent: User agent string
        max_pages: Maximum number of pages to crawl

    Returns:
        Set of non-generic email addresses found
    """
    from .scanner import DEFAULT_USER_AGENT

    if user_agent is None:
        user_agent = DEFAULT_USER_AGENT

    headers = {"User-Agent": user_agent}
    all_emails = set()
    visited_urls = set()
    urls_to_visit = set()

    # Start with emails from the homepage
    all_emails.update(extract_emails_from_html(initial_html, domain))
    visited_urls.add(base_url)

    # Get initial links
    internal_links = get_internal_links(initial_html, base_url, domain)

    # Prioritize contact-related pages
    parsed_base = urlparse(base_url)
    for path in CONTACT_PATHS:
        contact_url = f"{parsed_base.scheme}://{parsed_base.netloc}{path}"
        urls_to_visit.add(contact_url)

    # Add other internal links
    urls_to_visit.update(internal_links)

    # Crawl additional pages
    pages_crawled = 1
    while urls_to_visit and pages_crawled < max_pages:
        url = urls_to_visit.pop()

        if url in visited_urls:
            continue

        visited_urls.add(url)

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "text/html" in content_type:
                    all_emails.update(extract_emails_from_html(response.text, domain))
                    pages_crawled += 1

        except requests.RequestException:
            # Skip pages that fail to load
            continue

    return all_emails
