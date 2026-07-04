#!/usr/bin/env python3
"""
Automated mailto verification via macOS Mail.app (optional test #6).
Opens a mailto URL, reads the compose window, and reports integrity checks.
"""

import json
import re
import subprocess
import time
from pathlib import Path

EXPECTED_SUBJECT = "Support AB 123 — Tenant Protections Vote This Week"
EXPECTED_BCC_COUNT = 25


def load_urls() -> dict:
    data = json.loads((Path(__file__).parent / "mailto-urls.json").read_text())
    return {v["bccSeparator"]: v["url"] for v in data["versions"]}


def run_applescript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "AppleScript failed")
    return result.stdout.strip()


def close_compose_windows() -> None:
    run_applescript(
        """
        tell application "Mail"
            try
                repeat with w in windows
                    try
                        close w saving no
                    end try
                end repeat
            end try
        end tell
        """
    )


def open_mailto(url: str) -> None:
    subprocess.run(["open", url], check=True)
    time.sleep(3)


def read_compose_state() -> dict:
    raw = run_applescript(
        """
        tell application "Mail"
            set winCount to count of windows
            if winCount is 0 then return "NO_WINDOW"
            set m to missing value
            repeat with w in windows
                try
                    set msgList to (messages of w)
                    if (count of msgList) > 0 then
                        set m to item 1 of msgList
                        exit repeat
                    end if
                end try
            end repeat
            if m is missing value then return "NO_MESSAGE"
            set subj to subject of m
            set bodyText to content of m
            set bccList to {}
            repeat with r in (every bcc recipient of m)
                set end of bccList to address of r
            end repeat
            set AppleScript's text item delimiters to "|||"
            set bccJoined to bccList as text
            return subj & "###SUBJ###" & bccJoined & "###BCC###" & bodyText
        end tell
        """
    )
    if raw == "NO_WINDOW":
        return {"opened": False, "reason": "no Mail window appeared"}
    if raw == "NO_MESSAGE":
        return {"opened": False, "reason": "Mail window opened but no message found"}
    parts = raw.split("###BCC###", 1)
    head = parts[0]
    body = parts[1] if len(parts) > 1 else ""
    subj_part, _, bcc_part = head.partition("###SUBJ###")
    bcc_addresses = [a.strip() for a in bcc_part.split("|||") if a.strip()]
    return {
        "opened": True,
        "subject": subj_part.strip(),
        "bccCount": len(bcc_addresses),
        "bccAddresses": bcc_addresses,
        "body": body,
    }


def check_formatting(body: str) -> dict:
    return {
        "lineBreaksPreserved": body.count("\n") >= 4,
        "bulletsPresent": "•" in body,
        "doubleParagraphBreaks": "\n\n" in body,
    }


def grade(state: dict) -> str:
    if not state.get("opened"):
        reason = state.get("reason", "no compose window")
        return f"❌ failed — {reason}"
    issues = []
    if state["bccCount"] != EXPECTED_BCC_COUNT:
        issues.append(f"BCC {state['bccCount']}/{EXPECTED_BCC_COUNT}")
    if state["subject"] != EXPECTED_SUBJECT:
        issues.append(f"subject got '{state['subject'][:60]}'")
    fmt = state["formatting"]
    if not fmt["lineBreaksPreserved"]:
        issues.append("line breaks lost")
    if not fmt["bulletsPresent"]:
        issues.append("bullets missing")
    if issues:
        return "⚠️ partial — " + "; ".join(issues)
    return "✅ clean"


def test_variant(separator: str, url: str) -> dict:
    close_compose_windows()
    open_mailto(url)
    state = read_compose_state()
    if state.get("opened"):
        state["formatting"] = check_formatting(state["body"])
    state["grade"] = grade(state)
    state["separator"] = separator
    close_compose_windows()
    return state


def main() -> None:
    urls = load_urls()
    results = {}
    for sep in [",", ";"]:
        label = "comma" if sep == "," else "semicolon"
        print(f"Testing macOS Mail — {label} BCC...")
        try:
            results[label] = test_variant(sep, urls[sep])
        except Exception as exc:
            results[label] = {"grade": f"❌ failed — {exc}", "error": str(exc)}
        print(f"  Result: {results[label].get('grade', results[label])}")
        if results[label].get("bccCount") is not None:
            print(f"  BCC count: {results[label]['bccCount']}")
        if results[label].get("formatting"):
            print(f"  Formatting: {results[label]['formatting']}")

    out = Path(__file__).parent / "macos-mail-results.json"
    summary = {
        k: {
            "grade": v.get("grade"),
            "opened": v.get("opened"),
            "bccCount": v.get("bccCount"),
            "subject": v.get("subject"),
            "formatting": v.get("formatting"),
            "error": v.get("error"),
            "reason": v.get("reason"),
        }
        for k, v in results.items()
    }
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
