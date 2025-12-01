#!/usr/bin/env python3
"""
Script to update the disposable/honeypot email domains blocklist.

This script fetches domain lists from multiple sources and combines them
into a single blocklist file used by the email extractor to filter out
disposable/honeypot email addresses.

Usage:
    python scripts/update_disposable_blocklist.py

Sources:
    - disposable-email-domains/disposable-email-domains
    - unkn0w/disposable-email-domain-list
"""

import json
import os
import sys

import requests


# Blocklist sources
SOURCES = [
    "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf",
    "https://raw.githubusercontent.com/unkn0w/disposable-email-domain-list/main/domains.txt",
]

# Output path
OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "config",
    "disposable_email_blocklist.json"
)


def fetch_domains() -> set:
    """Fetch domains from all sources."""
    domains = set()
    
    for url in SOURCES:
        try:
            print(f"Fetching: {url}")
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    d = line.strip()
                    if d and not d.startswith("#"):
                        domains.add(d.lower())
                print(f"  ✓ Loaded successfully")
            else:
                print(f"  ✗ HTTP {resp.status_code}")
        except requests.RequestException as e:
            print(f"  ✗ Failed: {e}")
    
    return domains


def main():
    """Main entry point."""
    print("Updating disposable email domains blocklist...")
    print()
    
    domains = fetch_domains()
    
    if not domains:
        print("\nError: No domains fetched. Aborting update.")
        sys.exit(1)
    
    print(f"\nTotal unique domains: {len(domains)}")
    
    # Save to file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(domains), f, indent=2)
    
    print(f"Saved to: {OUTPUT_PATH}")
    print("Done!")


if __name__ == "__main__":
    main()
