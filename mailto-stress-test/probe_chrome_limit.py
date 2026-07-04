#!/usr/bin/env python3
"""
Probe Chrome's mailto URL length limit by testing incremental BCC counts.
Determines at what recipient count Chrome/Gmail stops passing parameters.
"""

import json
import subprocess
import time
import urllib.parse
from pathlib import Path

from generate_mailto import BCC_ADDRESSES, SUBJECT, BODY, build_mailto


def chrome_compose_tabs() -> list[str]:
    script = """
    tell application "Google Chrome"
        set matches to {}
        repeat with w in windows
            repeat with t in tabs of w
                set u to URL of t
                if u contains "view=cm" or u contains "extsrc=mailto" or u contains "tf=cm" then
                    set end of matches to u
                end if
            end repeat
        end repeat
        set AppleScript's text item delimiters to "|||"
        return matches as text
    end tell
    """
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    raw = result.stdout.strip()
    return [u for u in raw.split("|||") if u] if raw else []


def count_bcc_in_gmail_url(url: str) -> int:
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    if "url" in params:
        inner = urllib.parse.urlparse(params["url"][0])
        params = urllib.parse.parse_qs(inner.query)
    bcc = params.get("bcc", [""])[0]
    return len([x for x in bcc.replace(";", ",").split(",") if x.strip()])


def test_count(n: int) -> dict:
    bcc = ",".join(BCC_ADDRESSES[:n])
    query = urllib.parse.urlencode({"bcc": bcc, "subject": SUBJECT, "body": BODY})
    url = f"mailto:?{query}"
    subprocess.run(["open", url])
    time.sleep(3)
    tabs = chrome_compose_tabs()
    return {
        "bccCount": n,
        "mailtoLength": len(url),
        "composeTabsFound": len(tabs),
        "composeUrlLengths": [len(t) for t in tabs],
        "bccInComposeUrl": count_bcc_in_gmail_url(tabs[0]) if tabs else 0,
        "composeUrlPreview": tabs[0][:200] if tabs else None,
    }


def main() -> None:
    if not Path("/Applications/Google Chrome.app").exists():
        print("Chrome not installed")
        return

    # Probe key thresholds near the 2000-char cliff
    thresholds = [1, 3, 5, 10, 15, 20, 23, 25]
    results = []
    for n in thresholds:
        print(f"Testing {n} BCC recipients (mailto ~{len(build_mailto(',').replace(BCC_ADDRESSES[0], BCC_ADDRESSES[0]))} chars)...")
        r = test_count(n)
        results.append(r)
        print(f"  mailto length: {r['mailtoLength']}, compose tabs: {r['composeTabsFound']}, bcc in URL: {r['bccInComposeUrl']}")
        time.sleep(1)

    out = Path(__file__).parent / "chrome-length-probe.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
