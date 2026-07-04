#!/usr/bin/env python3
"""Unit tests for campaign codec (mirrors lib/campaignCodec.js)."""

import base64
import json
from pathlib import Path

from test_build_mailto import load_campaign


def encode_campaign(campaign: dict) -> str:
    payload = json.dumps(
        {
            "t": campaign.get("title", ""),
            "s": campaign["subject"],
            "b": campaign["body"],
            "r": campaign["recipients"],
            "c": campaign.get("ctaLabel", ""),
        },
        separators=(",", ":"),
    )
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


def decode_campaign(encoded: str) -> dict:
    if not encoded:
        raise ValueError("No campaign data in link.")

    pad = "=" * (-len(encoded) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(encoded + pad).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError("Could not read campaign data. The link may be corrupted.") from e

    if not data.get("s") or not data.get("b") or not data.get("r"):
        raise ValueError("Invalid campaign data in link.")

    return {
        "title": data.get("t") or "Email your representatives",
        "subject": str(data["s"]),
        "body": str(data["b"]),
        "recipients": data["r"],
        "ctaLabel": data.get("c") or "Email your representatives",
    }


def test_roundtrip():
    campaign = load_campaign()
    encoded = encode_campaign(campaign)
    decoded = decode_campaign(encoded)
    assert decoded["subject"] == campaign["subject"]
    assert decoded["body"] == campaign["body"]
    assert decoded["recipients"] == campaign["recipients"]


def test_rejects_empty_hash():
    try:
        decode_campaign("")
        assert False, "Should have raised"
    except ValueError as e:
        assert "No campaign data" in str(e)


def test_rejects_corrupt_hash():
    try:
        decode_campaign("not-valid-base64!!!")
        assert False, "Should have raised"
    except ValueError as e:
        assert "corrupted" in str(e)


def test_rejects_missing_fields():
    encoded = encode_campaign({"title": "x", "subject": "", "body": "y", "recipients": []})
    try:
        decode_campaign(encoded)
        assert False, "Should have raised"
    except ValueError as e:
        assert "Invalid campaign data" in str(e)


if __name__ == "__main__":
    tests = [
        test_roundtrip,
        test_rejects_empty_hash,
        test_rejects_corrupt_hash,
        test_rejects_missing_fields,
    ]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"\nAll {len(tests)} tests passed.")
