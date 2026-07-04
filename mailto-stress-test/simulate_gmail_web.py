#!/usr/bin/env python3
"""
Parse mailto URL the way Gmail's web handler does and verify parameter survival.
Simulates Chrome handing off mailto to Gmail (view=cm compose URL).
"""

import json
import urllib.parse
from pathlib import Path


def gmail_compose_url_from_mailto(mailto: str) -> dict:
    """Gmail web handler pattern: view=cm with individual query params."""
    parsed = urllib.parse.urlparse(mailto)
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

    bcc = params.get("bcc", [""])[0]
    subject = params.get("subject", [""])[0]
    body = params.get("body", [""])[0]

    gmail_params = {
        "view": "cm",
        "fs": "1",
        "bcc": bcc,
        "su": subject,
        "body": body,
    }
    base = "https://mail.google.com/mail/?"
    gmail_url = base + urllib.parse.urlencode(gmail_params)

    bcc_count = len([x for x in bcc.replace(";", ",").split(",") if x.strip()])
    return {
        "gmailUrlLength": len(gmail_url),
        "bccCount": bcc_count,
        "subject": subject,
        "bodyLength": len(body),
        "bodyHasDoubleNewlines": "\n\n" in body,
        "bodyHasBullets": "•" in body,
        "bodyPreview": body[:200],
    }


def main() -> None:
    data = json.loads((Path(__file__).parent / "mailto-urls.json").read_text())
    results = {}
    for v in data["versions"]:
        key = "comma" if v["bccSeparator"] == "," else "semicolon"
        results[key] = {
            "mailtoLength": v["totalLength"],
            **gmail_compose_url_from_mailto(v["url"]),
        }

    print("=== Gmail Web Handler Simulation ===\n")
    for key, r in results.items():
        print(f"{key} BCC:")
        print(f"  mailto length: {r['mailtoLength']}")
        print(f"  Gmail compose URL length: {r['gmailUrlLength']}")
        print(f"  BCC count after parse: {r['bccCount']}")
        print(f"  Subject intact: {r['subject'] == data['subject']}")
        print(f"  Body length: {r['bodyLength']}")
        print(f"  Line breaks preserved in parse: {r['bodyHasDoubleNewlines']}")
        print(f"  Bullets preserved in parse: {r['bodyHasBullets']}")
        print()

    out = Path(__file__).parent / "gmail-web-simulation.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
