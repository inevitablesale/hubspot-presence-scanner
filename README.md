# HubSpot Presence Scanner

Lightweight domain crawler that detects HubSpot usage across business websites by scanning for tracking codes, COS signatures, embedded forms, script tags, and API endpoints. When HubSpot is detected, it also crawls the site to find non-generic email addresses. Built for consultants, revops teams, and automation workflows that need to identify HubSpot-powered organizations at scale.

## Features

- **HubSpot Detection**: Scans HTML, script tags, metadata, and HTTP headers for HubSpot signatures
- **Confidence Scoring**: Returns a 0-100 confidence score based on detected signals
- **Portal ID Extraction**: Identifies HubSpot portal IDs when available
- **Email Extraction**: Crawls sites with HubSpot to find non-generic business emails
- **Generic Email Filtering**: Automatically excludes info@, support@, admin@, hello@, sales@, etc.
- **JSON Output**: Structured output with domain, signals, emails, and confidence scores
- **CLI & Library**: Use as command-line tool or import as Python library

## Installation

```bash
# Clone the repository
git clone https://github.com/inevitablesale/hubspot-presence-scanner.git
cd hubspot-presence-scanner

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

### Command Line

```bash
# Scan a single domain
hubspot-scanner hubspot.com

# Scan multiple domains
hubspot-scanner hubspot.com drift.com example.com

# Scan domains from a file
hubspot-scanner -f examples/domains.txt

# Save results to JSON file
hubspot-scanner -f examples/domains.txt -o results.json

# Skip email extraction (faster)
hubspot-scanner hubspot.com --no-emails

# Increase pages crawled for emails
hubspot-scanner hubspot.com --max-pages 20
```

### Python Library

```python
from hubspot_scanner import scan_domain, scan_domains

# Scan a single domain
result = scan_domain("hubspot.com")
print(f"HubSpot detected: {result.hubspot_detected}")
print(f"Confidence: {result.confidence_score}%")
print(f"Emails: {result.emails}")

# Scan multiple domains
results = scan_domains(["hubspot.com", "drift.com", "example.com"])
for r in results:
    if r["hubspot_detected"]:
        print(f"{r['domain']}: {r['confidence_score']}% - Emails: {r['emails']}")
```

## Output Format

The scanner outputs structured JSON with the following fields:

```json
{
  "domain": "example.com",
  "hubspot_detected": true,
  "confidence_score": 95.0,
  "hubspot_signals": [
    {
      "name": "hs-script-loader",
      "description": "HubSpot tracking script loader",
      "weight": 30,
      "portal_id": "12345"
    }
  ],
  "portal_ids": ["12345"],
  "emails": ["john.smith@example.com", "jane.doe@example.com"],
  "error": null
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | The scanned domain |
| `hubspot_detected` | boolean | Whether HubSpot was detected |
| `confidence_score` | float | Confidence score (0-100) |
| `hubspot_signals` | array | List of detected HubSpot signatures |
| `portal_ids` | array | HubSpot portal IDs found |
| `emails` | array | Non-generic emails found (only if HubSpot detected) |
| `error` | string/null | Error message if scan failed |

## Detection Signals

The scanner looks for these HubSpot signatures:

### Script Tags
- `js.hs-scripts.com` - HubSpot tracking script loader
- `js.hs-analytics.net` - HubSpot analytics
- `track.hubspot.com` - Tracking endpoint
- `js.hsforms.net` - HubSpot forms
- `js.hscta.net` - Call-to-action scripts

### COS (Content Optimization System)
- `cdn2.hubspot.net` - HubSpot CDN
- `/hubfs/` - HubSpot File System
- `hs-cos-wrapper` - COS wrapper classes
- `hs-menu-wrapper` - Menu components

### API & Endpoints
- `api.hubspot.com` - API calls
- `forms.hubspot.com` - Form submissions

### Inline JavaScript
- `_hsq` - HubSpot tracking queue
- `hbspt.` - HubSpot JavaScript object

## Email Filtering

When HubSpot is detected, the scanner crawls the site for email addresses. Generic emails are automatically excluded:

- info@, support@, admin@
- hello@, sales@, contact@
- help@, noreply@, webmaster@
- office@, team@, general@

## CLI Options

```
usage: hubspot-scanner [-h] [-f DOMAINS_FILE] [-o OUTPUT_FILE] [-t TIMEOUT]
                       [--user-agent USER_AGENT] [-q] [--no-summary]
                       [--compact] [--no-emails] [--max-pages MAX_PAGES] [-v]
                       [domains ...]

Options:
  domains               Domain(s) to scan
  -f, --file            File containing domains (one per line)
  -o, --output          Output file for JSON results
  -t, --timeout         Request timeout in seconds (default: 10)
  --user-agent          Custom user agent string
  -q, --quiet           Suppress progress output
  --no-summary          Suppress summary output
  --compact             Output compact JSON
  --no-emails           Skip email extraction
  --max-pages           Max pages to crawl for emails (default: 10)
  -v, --version         Show version
```

## Examples

See the `examples/` directory for more usage examples:

- `basic_usage.py` - Single domain scanning
- `batch_scan.py` - Multiple domain scanning with progress
- `domains.txt` - Sample domain list
- `sample_output.json` - Example output format

## Use Cases

- **Lead Generation**: Find HubSpot users and extract contact emails
- **Competitive Analysis**: Identify which competitors use HubSpot
- **Market Research**: Survey HubSpot adoption across industries
- **Integration Planning**: Identify potential integration partners
- **RevOps Workflows**: Automate HubSpot user identification

## Requirements

- Python 3.10+
- requests
- beautifulsoup4
- lxml

## License

MIT License
