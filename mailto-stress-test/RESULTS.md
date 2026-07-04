# LA Forward Mailto Stress Test — Results

**Date:** 2026-07-02  
**Campaign:** AB 123 tenant protections (realistic advocacy email)  
**Test artifacts:** `index.html`, `mailto-urls.json`, `generate_mailto.py`

---

## Executive summary

**Verdict: All P1 clients pass with comma separator and `%20` encoding.** Plain mailto architecture is viable for LA Forward's client mix.

**Product cap: 21 recipients per campaign (hard limit).** No overflow — campaigns with > 21 are rejected at build time.

| Metric | Value |
|---|---|
| One-click max BCC | **21** |
| Stress-test max verified | 25 (all P1 pass) |
| Separator | Comma |
| **Mailto URL length at 21 BCC (`%20`)** | **~2,300 chars** |
| Encoding requirement | **`%20` for spaces — never `+`** |

### Final test matrix (2026-07-02, after `%20` fix)

| # | Client | Opens | 25 BCC | Formatting | Verdict |
|---|---|---|---|---|---|
| 1 | Gmail — web, Chrome desktop | ✅ | ✅ | ✅ | **✅ clean** |
| 2 | Gmail app — iOS | ✅ | ✅ | ✅ | **✅ clean** |
| 3 | Native Mail app — iOS | ✅ | ✅ | ✅ | **✅ clean** |

**Key bug found and fixed:** Default URL encoders (`URLSearchParams`, Python `urlencode`) use `+` for spaces. Gmail web leaves `+` literal in subject/body. Replacing `+` → `%20` fixes formatting on all three clients.

**PRD cap: 21 BCC one-click.** Overflow recipients use copy-paste block. `%20` encoding required.

---

## URL length cliff (computed, not guessed)

With this exact subject + body, mailto length grows with BCC count:

| BCC count | mailto length | Under 2,000? |
|---:|---:|:---:|
| 1 | 1,330 | ✅ |
| 10 | 1,611 | ✅ |
| 15 | 1,786 | ✅ |
| 20 | 1,936 | ✅ |
| **21** | **1,967** | **✅ (last safe)** |
| **22** | **2,008** | **❌** |
| 23 | 2,039 | ❌ |
| 24 | 2,070 | ❌ |
| **25** | **2,101** | **❌** |

Real legislator emails (longer domains, longer lists) could push the safe count lower.

---

## Test matrix (final)

### Required (P1) — all pass

| # | Client / Device | Priority | Comma BCC | Semicolon BCC | Notes |
|---|---|---|---|---|---|
| 1 | Gmail — web, Chrome desktop | **Required** | **✅ clean** | — skip — | 25 BCC, formatting correct after `%20` fix |
| 2 | Gmail app — iOS | **Required** | **✅ clean** | — skip — | Confirmed 2026-07-02 |
| 3 | Native Mail app — iOS (Safari link) | **Required** | **✅ clean** | — skip — | Confirmed 2026-07-02 |

### Optional

| # | Client / Device | Priority | Comma BCC | Semicolon BCC | Notes |
|---|---|---|---|---|---|
| 4 | Gmail app — Android | Optional | — skip — | — skip — | No Android device available |
| 5 | Outlook desktop — Chrome default handler | Optional | — skip — | — skip — | Outlook not installed on test machine |
| 6 | Native Mail app — macOS Safari | Optional | ❌ auto failed | ❌ auto failed | Mail.app AppleScript API returned errors on macOS 26.5; could not read compose window programmatically |

---

## What we verified with evidence

### ✅ URL encoding integrity (both separators)

- All 25 BCC addresses present in generated URL (verified via parse)
- Subject decodes to: `Support AB 123 — Tenant Protections Vote This Week`
- Body retains `\n\n` paragraph breaks and `•` bullet characters after URL decode
- Gmail web handler **simulation** (parse mailto → Gmail `view=cm` params): all 25 BCC, subject, body, bullets, and line breaks survive parsing — **if the full URL reaches Gmail intact**

### ⚠️ Chrome + Gmail web (partial / inconclusive)

- Gmail is registered as Chrome's mailto handler on test machine
- Clicking 2,101-char mailto did **not** produce a tab with `view=cm` query params (compose may open as overlay/draft with params already consumed)
- Could not read compose DOM — Chrome requires **View → Developer → Allow JavaScript from Apple Events** for automated inspection
- **Manual check needed:** open compose after click, count BCC chips, verify body formatting

### ❌ Automated macOS Mail test

AppleScript against Mail.app failed (`every window doesn't understand the "count" message`). Not a product failure signal — automation limitation only.

---

## Manual test checklist (per cell)

For each link click, record:

1. **Opens?** nothing / error / blank compose / populated compose  
2. **BCC count** — must be **25** (silent drops are the dangerous failure)  
3. **Formatting** — paragraph breaks, bullets (`•`), no words running together  
4. **Subject** — full line: `Support AB 123 — Tenant Protections Vote This Week`

Shorthand: ✅ clean / ⚠️ partial (note what broke) / ❌ failed

---

## How to run manual tests

1. Open test page (already opened in Chrome on this machine):
   ```
   file:///Users/cnibungco/Documents/la_forward/mailto-stress-test/index.html
   ```
2. Click **Open compose (comma BCC)** — verify four checks above  
3. Discard draft, click **Open compose (semicolon BCC)** — repeat  
4. On iPhone: AirDrop or iMessage the `index.html` file, open in **Safari**, repeat for Gmail app and Mail app

**A/B at the cliff:** The page also includes 21-recipient links (under 2,000 chars) if you want to confirm whether failures at 25 disappear at 21.

---

## Slack gut-check for Godfrey/Jason

> Quick question before we lock mailto architecture: is the member base actually iPhone + Gmail heavy (Gmail app + Safari + Gmail web), or do a meaningful number use Android, Outlook, or desktop native clients? We're stress-testing 25-recipient BCC mailto on those three iOS/Gmail paths — want to make sure we're testing the right matrix.

---

## Reading the results (for PRD author)

**Outcome: All P1 rows ✅ at 25 BCC.**

| Decision | Value |
|---|---|
| Architecture | Plain `mailto:` link — no server-side send, no cap |
| BCC separator | Comma |
| Max recipients | **21** (hard limit, no overflow) |
| URL encoding | **`%20` for spaces, `%0A` for line breaks** — never `+` |
| Semicolon fallback | Not needed |
| Copy-paste fallback | Optional safety net for edge clients (Outlook, Android) — not required for P1 mix |

### Implementation note (must ship)

```javascript
// After building query string, always:
queryString.replace(/\+/g, "%20");
```

Default `URLSearchParams.toString()` and Python `urllib.parse.urlencode()` will break Gmail web without this.

---

## Files

| File | Purpose |
|---|---|
| `index.html` | Click-to-test page with both mailto variants |
| `campaign.js` | Shared subject, BCC list, body |
| `mailto-urls.json` | Generated URLs + length metadata |
| `generate_mailto.py` | Regenerate URLs / recompute length table |
| `simulate_gmail_web.py` | Gmail handler parse simulation |
| `gmail-web-simulation.json` | Simulation output |
