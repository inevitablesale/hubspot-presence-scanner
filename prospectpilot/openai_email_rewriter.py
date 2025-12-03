# prospectpilot/openai_email_rewriter.py

import json
import logging
import os
from typing import Dict, Tuple

try:
    from openai import OpenAI
except ImportError:  # soft dependency, we fail gracefully
    OpenAI = None  # type: ignore

logger = logging.getLogger(__name__)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_EMAIL_TEMPERATURE = float(os.getenv("OPENAI_EMAIL_TEMPERATURE", "0.4"))
OPENAI_EMAIL_MAX_TOKENS = int(os.getenv("OPENAI_EMAIL_MAX_TOKENS", "400"))


_client = None


def _get_client():
    """
    Lazy-init OpenAI client. Returns None if API key or library is missing.
    """
    global _client

    if _client is not None:
        return _client

    api_key = os.getenv("OPENAI_API_KEY")
    if OpenAI is None:
        logger.warning(
            "openai package not installed; skipping email rewrite. "
            "Install with `pip install openai`."
        )
        return None

    if not api_key:
        logger.warning(
            "OPENAI_API_KEY not set; skipping email rewrite "
            "(email will still be sent with original template)."
        )
        return None

    _client = OpenAI(api_key=api_key)
    return _client


SYSTEM_PROMPT = """
You are an email deliverability and outbound copywriting specialist.

You take a short, already-structured cold email and:
- keep it SHORT (approximately 80–140 words)
- keep the tone professional, friendly, and conversational
- avoid all spammy signals ("FREE", "guarantee", excessive hype, ALL CAPS, etc.)
- preserve intent: this is a real technical consultant/agency offering help
- avoid heavy formatting (no bullet spam, no long walls of text)
- keep links EXACTLY as provided (do not change URLs)
- keep names, company name, city, hourly rate EXACTLY as provided
- avoid emojis, images, and exaggerated claims.

You must:
- return valid JSON with keys: "subject" and "body"
- keep the subject line short and natural (3–7 words ideally)
- keep the body as a plain-text email (no HTML), with sensible line breaks.
""".strip()


def rewrite_email_with_openai(
    subject: str,
    body: str,
    context: Dict[str, str],
) -> Tuple[str, str, Dict[str, object]]:
    """
    Rewrite subject/body via OpenAI for deliverability & clarity.
    If anything fails (no key, bad response, exception), returns original
    subject/body and a metadata dict indicating rewrite_failed.

    context example:
      {
        "domain": "example.com",
        "persona": "Scott",
        "persona_email": "scott@closespark.co",
        "persona_role": "Systems Engineer",
        "company_name": "CloseSpark",
        "company_location": "Richmond, VA",
        "company_rate": "$85/hr",
        "main_tech": "Shopify",
        "variant_id": "shopify_v2",
      }
    """
    client = _get_client()
    meta: Dict[str, object] = {
        "rewrite_model": OPENAI_MODEL,
        "rewrite_temperature": OPENAI_EMAIL_TEMPERATURE,
        "rewrite_used": False,
    }

    if client is None:
        meta["rewrite_reason"] = "no_client"
        return subject, body, meta

    # Build a compact description of the situation for the model
    user_payload = {
        "original_subject": subject,
        "original_body": body,
        "context": context,
        "instructions": {
            "keep_links_exact": True,
            "keep_names_company_rate_exact": True,
            "max_word_range": "80-140",
            "no_html": True,
        },
    }

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=OPENAI_EMAIL_TEMPERATURE,
            max_tokens=OPENAI_EMAIL_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(user_payload),
                },
            ],
        )

        raw = response.choices[0].message.content or ""
        data = json.loads(raw)

        new_subject = data.get("subject", subject) or subject
        new_body = data.get("body", body) or body

        new_subject = str(new_subject).strip()
        new_body = str(new_body).strip()

        # Log the generated email template
        logger.info(
            "Email template generated for domain=%s, primary_email=%s:\n%s\n%s",
            context.get("domain", "unknown"),
            context.get("persona_email", "unknown"),
            "-" * 60,
            new_body,
        )

        meta["rewrite_used"] = True
        meta["rewrite_reason"] = "success"
        return new_subject, new_body, meta

    except Exception as e:
        logger.warning("OpenAI email rewrite failed: %s", e, exc_info=True)
        meta["rewrite_reason"] = f"error: {e}"
        return subject, body, meta
