#!/usr/bin/env python3
"""Unit tests for mailto URL builder (mirrors lib/buildMailtoUrl.js)."""

import json
import re
import urllib.parse
from pathlib import Path

MAX_RECIPIENTS = 21
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def build_mailto_url(campaign: dict) -> str:
    recipients = campaign["recipients"]
    if not recipients:
        raise ValueError("Campaign must include at least one recipient.")
    if len(recipients) > MAX_RECIPIENTS:
        raise ValueError(
            f"Campaign has {len(recipients)} recipients; maximum is {MAX_RECIPIENTS}."
        )
    for i, email in enumerate(recipients):
        if not EMAIL_RE.match(email):
            raise ValueError(f"Invalid email at index {i}: {email}")

    query = urllib.parse.urlencode(
        {
            "bcc": ",".join(recipients),
            "subject": campaign["subject"],
            "body": campaign["body"],
        }
    ).replace("+", "%20")
    return f"mailto:?{query}"


def load_campaign():
    return json.loads((Path(__file__).parent.parent / "campaigns" / "ab123.json").read_text())


def test_spaces_use_percent20_not_plus():
    url = build_mailto_url(load_campaign())
    assert "+" not in url, f"URL must not contain + signs: {url[:200]}"


def test_line_breaks_encoded():
    url = build_mailto_url(load_campaign())
    assert "%0A" in url


def test_21_recipients_in_bcc():
    campaign = load_campaign()
    assert len(campaign["recipients"]) == 21
    url = build_mailto_url(campaign)
    parsed = urllib.parse.urlparse(url)
    bcc = urllib.parse.parse_qs(parsed.query)["bcc"][0]
    assert len(bcc.split(",")) == 21


def test_rejects_more_than_21():
    campaign = load_campaign()
    campaign["recipients"] = campaign["recipients"] + ["extra@example.com"]
    try:
        build_mailto_url(campaign)
        assert False, "Should have raised"
    except ValueError as e:
        assert "maximum is 21" in str(e)


def test_subject_and_body_round_trip():
    campaign = load_campaign()
    url = build_mailto_url(campaign)
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    assert params["subject"][0] == campaign["subject"]
    assert params["body"][0] == campaign["body"]


def test_url_length_under_2500():
    url = build_mailto_url(load_campaign())
    assert len(url) < 2500, f"URL too long: {len(url)}"


if __name__ == "__main__":
    tests = [
        test_spaces_use_percent20_not_plus,
        test_line_breaks_encoded,
        test_21_recipients_in_bcc,
        test_rejects_more_than_21,
        test_subject_and_body_round_trip,
        test_url_length_under_2500,
    ]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"\nAll {len(tests)} tests passed.")
