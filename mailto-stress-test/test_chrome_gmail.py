#!/usr/bin/env python3
"""
Test mailto handoff via Chrome on macOS.
Checks whether Chrome opens Gmail compose or native handler, and tab URL length.
"""

import json
import subprocess
import time
import urllib.parse
from pathlib import Path


def run_applescript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def chrome_installed() -> bool:
    return Path("/Applications/Google Chrome.app").exists()


def get_chrome_active_url() -> str:
    return run_applescript(
        """
        tell application "Google Chrome"
            if (count of windows) = 0 then return "NO_WINDOW"
            return URL of active tab of front window
        end tell
        """
    )


def open_mailto_in_chrome(url: str) -> None:
    # Navigate active tab to mailto — triggers registered protocol handler
    escaped = url.replace("\\", "\\\\").replace('"', '\\"')
    run_applescript(
        f"""
        tell application "Google Chrome"
            activate
            if (count of windows) = 0 then
                make new window
            end if
            set URL of active tab of front window to "{escaped}"
        end tell
        """
    )
    time.sleep(4)


def analyze_gmail_url(url: str) -> dict:
    if not url.startswith("http"):
        return {"handler": "non-http", "raw": url[:200]}
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    bcc = params.get("bcc", params.get("bcc", [""]))
    if not bcc:
        bcc = params.get("bcc", [""])
    # Gmail uses bcc in some flows, or embeds mailto in url param
    mailto_embed = params.get("url", [""])[0]
    if mailto_embed.startswith("mailto:"):
        inner = urllib.parse.urlparse(mailto_embed)
        inner_params = urllib.parse.parse_qs(inner.query)
        bcc_raw = inner_params.get("bcc", [""])[0]
        subject = inner_params.get("subject", [""])[0]
        body = inner_params.get("body", [""])[0]
    else:
        bcc_raw = params.get("bcc", [""])[0]
        subject = params.get("su", params.get("subject", [""]))[0]
        body = params.get("body", [""])[0]

    bcc_count = len([x for x in bcc_raw.replace(";", ",").split(",") if x.strip()]) if bcc_raw else 0
    return {
        "handler": "gmail-web" if "mail.google.com" in url else "other-http",
        "urlLength": len(url),
        "bccCount": bcc_count,
        "subjectPresent": bool(subject),
        "subject": subject[:80],
        "bodyLength": len(body),
        "bodyHasBullets": "•" in body,
        "bodyHasNewlines": "\n" in body or "%0A" in url,
        "truncatedSuspect": len(url) < 500 and bcc_count == 0,
    }


def main() -> None:
    if not chrome_installed():
        print("Chrome not installed — skipping")
        return

    data = json.loads((Path(__file__).parent / "mailto-urls.json").read_text())
    results = {}
    for v in data["versions"]:
        key = "comma" if v["bccSeparator"] == "," else "semicolon"
        print(f"Opening in Chrome: {key} BCC...")
        try:
            open_mailto_in_chrome(v["url"])
            url = get_chrome_active_url()
            analysis = analyze_gmail_url(url)
            analysis["finalUrlPreview"] = url[:250]
            results[key] = analysis
            print(f"  Active URL length: {analysis.get('urlLength', 'n/a')}")
            print(f"  Handler: {analysis.get('handler')}")
            print(f"  BCC count in URL: {analysis.get('bccCount')}")
        except Exception as exc:
            results[key] = {"error": str(exc)}
            print(f"  Error: {exc}")

    out = Path(__file__).parent / "chrome-gmail-results.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
