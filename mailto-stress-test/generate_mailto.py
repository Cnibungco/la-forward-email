#!/usr/bin/env python3
"""Generate and analyze mailto stress-test URLs."""

import json
import urllib.parse
from pathlib import Path

SUBJECT = "Support AB 123 — Tenant Protections Vote This Week"

BCC_ADDRESSES = [
    "asm.member001@assembly.ca.gov",
    "asm.member002@assembly.ca.gov",
    "asm.member003@assembly.ca.gov",
    "asm.member004@assembly.ca.gov",
    "asm.member005@assembly.ca.gov",
    "sen.member001@sen.ca.gov",
    "sen.member002@sen.ca.gov",
    "sen.member003@sen.ca.gov",
    "sen.member004@sen.ca.gov",
    "sen.member005@sen.ca.gov",
    "leg.aide001@legislature.ca.gov",
    "leg.aide002@legislature.ca.gov",
    "leg.aide003@legislature.ca.gov",
    "leg.aide004@legislature.ca.gov",
    "leg.aide005@legislature.ca.gov",
    "district.office001@ca.gov",
    "district.office002@ca.gov",
    "district.office003@ca.gov",
    "district.office004@ca.gov",
    "district.office005@ca.gov",
    "policy.staff001@assembly.ca.gov",
    "policy.staff002@assembly.ca.gov",
    "policy.staff003@sen.ca.gov",
    "policy.staff004@sen.ca.gov",
    "policy.staff005@sen.ca.gov",
]

BODY = """Dear Assemblymember,

I am writing as a constituent and LA Forward member to urge your support for AB 123, which strengthens tenant protections ahead of this week's floor vote.

Los Angeles renters are facing record displacement pressures. Without clear guardrails on no-fault evictions and rent gouging, families are being forced out of the neighborhoods they have built their lives in. This bill is a necessary step toward stability for working-class tenants across our district.

Please vote YES on AB 123. Specifically, I ask that you support:

• Just-cause eviction standards that prevent retaliatory displacement
• Limits on rent increases during declared housing emergencies
• Stronger enforcement so tenants can actually access the protections on paper
• Funding for legal aid so low-income renters aren't priced out of their rights

Housing is a human right, and your vote this week will directly determine whether thousands of Angelenos can stay housed. I hope I can count on your leadership.

Thank you for your time and service to our community.

Sincerely,
[Your Name]
[Your Address]
[Your Zip Code]"""


def build_mailto(separator: str, count=None) -> str:
    addrs = BCC_ADDRESSES if count is None else BCC_ADDRESSES[:count]
    bcc = separator.join(addrs)
    query = urllib.parse.urlencode({"bcc": bcc, "subject": SUBJECT, "body": BODY})
    # Gmail mailto leaves + literal — force %20 for spaces
    query = query.replace("+", "%20")
    return f"mailto:?{query}"


def analyze(label: str, url: str, separator: str) -> dict:
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    bcc_raw = params.get("bcc", [""])[0]
    if separator == ",":
        count = len([x for x in bcc_raw.split(",") if x])
    else:
        count = len([x for x in bcc_raw.split(";") if x])
    return {
        "label": label,
        "totalLength": len(url),
        "bccSeparator": separator,
        "bccCountInUrl": count,
        "subjectLength": len(SUBJECT),
        "bodyLength": len(BODY),
        "url": url,
    }


def main() -> None:
    comma = analyze("comma-separated BCC", build_mailto(","), ",")
    semicolon = analyze("semicolon-separated BCC", build_mailto(";"), ";")
    report = {
        "generatedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "subject": SUBJECT,
        "expectedBccCount": len(BCC_ADDRESSES),
        "versions": [comma, semicolon],
    }
    out = Path(__file__).parent / "mailto-urls.json"
    out.write_text(json.dumps(report, indent=2))
    print("=== LA Forward Mailto Stress Test URLs ===\n")
    for v in [comma, semicolon]:
        print(v["label"])
        print(f"  Total URL length: {v['totalLength']} chars")
        print(f"  BCC addresses encoded: {v['bccCountInUrl']}")
        print(f"  Subject length: {v['subjectLength']} chars")
        print(f"  Body length: {v['bodyLength']} chars")
        print(f"  URL preview (first 120): {v['url'][:120]}...")
        print()
    print(f"Full URLs written to {out}")


if __name__ == "__main__":
    main()
