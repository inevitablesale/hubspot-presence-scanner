"""HubSpot Presence Scanner - Detect HubSpot usage on websites."""

from .detector import HubSpotDetector, DetectionResult
from .scanner import scan_domains, scan_domain
from .email_extractor import (
    extract_emails_from_html,
    crawl_for_emails,
    is_disposable_email,
    load_disposable_domains,
)

__version__ = "1.0.0"
__all__ = [
    "HubSpotDetector",
    "DetectionResult",
    "scan_domains",
    "scan_domain",
    "extract_emails_from_html",
    "crawl_for_emails",
    "is_disposable_email",
    "load_disposable_domains",
]
