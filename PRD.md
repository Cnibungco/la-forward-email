# PRD: LA Forward One-Click Email

**Status:** Built  
**Date:** 2026-07-02  
**Evidence:** `mailto-stress-test/RESULTS.md`  
**Implementation:** `index.html` (organizer dashboard), `email.html` (shareable member page), `lib/buildMailtoUrl.js`, `lib/campaignCodec.js`  
**Stakeholders:** Godfrey, Jason, LA Forward members

---

## 1. Problem

LA Forward members send advocacy emails to legislators as part of campaigns. Today this requires manually copying recipient lists, subject lines, and formatted message bodies into their email client — friction that reduces participation.

Members primarily use **Gmail (web + iOS app)** and **native iOS Mail**, opened via mobile Safari.

---

## 2. Solution

**Organizer dashboard** (`index.html`): Jason/Godfrey enter campaign title, subject, body, and up to 21 BCC recipients, then click **Generate share link** to get a URL for social media.

**Member page** (`email.html`): Shared link opens a one-click button that pre-fills the member's email client with BCC, subject, and body.

Campaign data is encoded in the share link URL (no server required for v1).

---

## 3. Architecture decision

| Option | Decision | Rationale |
|---|---|---|
| Plain `mailto:` link | **Selected** | All P1 clients pass with correct formatting (stress-tested 2026-07-02) |
| Server-side send (API/form) | Rejected for v1 | Higher complexity, deliverability, and compliance overhead |
| **Hard cap at 21 BCC** | **Selected** | URL-length safety for untested clients; campaigns never exceed 21 |
| Semicolon BCC separator | **Not needed** | Comma works on all tested clients |

---

## 4. Stress test summary (evidence)

| Client | Opens compose | Formatting intact | Verdict |
|---|---|---|---|
| Gmail — web, Chrome | ✅ | ✅ | Pass |
| Gmail app — iOS | ✅ | ✅ | Pass |
| Native Mail app — iOS | ✅ | ✅ | Pass |

**Critical encoding rule:** Use `%20` for spaces, never `+`. Default URL encoders break Gmail web.

At **21 BCC** with `%20` encoding: **~2,300 characters**.

---

## 5. User stories

### Member

1. I tap **"Email your representatives"** and my email app opens with the message ready to send.
2. All legislators are in BCC (hidden from each other).
3. I edit the body to add my name and address before sending.
4. On iPhone, Gmail or Mail opens depending on my default — both work.

### Organizer (Godfrey/Jason)

1. I configure a campaign with subject, body, and **1–21 recipients**.
2. If a target list exceeds 21, I split it into separate campaigns.

---

## 6. Functional requirements

### 6.1 One-click button

- Primary CTA opens mail client via `mailto:` URI.
- Works from mobile Safari (iOS) and desktop Chrome (Gmail web handler).

### 6.2 Mailto URI construction

```
mailto:?bcc=<addr1>,<addr2>,...&subject=<encoded>&body=<encoded>
```

| Parameter | Rule |
|---|---|
| `bcc` | Comma-separated, **1–21** addresses |
| `subject` | Plain text, URL-encoded |
| `body` | Plain text, `%0A` line breaks, Unicode bullets allowed |
| `to` | Empty |

### 6.3 URL encoding (non-negotiable)

| Character | Encoding |
|---|---|
| Space | `%20` — **never `+`** |
| Line break | `%0A` |

```javascript
function buildMailtoUrl({ recipients, subject, body }) {
  const params = new URLSearchParams();
  params.set("bcc", recipients.join(","));
  params.set("subject", subject);
  params.set("body", body);
  return "mailto:?" + params.toString().replace(/\+/g, "%20");
}
```

### 6.4 Campaign content

| Field | Type | Constraints |
|---|---|---|
| `title` | string | Display |
| `ctaLabel` | string | Button text |
| `subject` | string | Recommend ≤ 80 chars |
| `body` | string | Plain text; placeholders OK |
| `recipients` | email[] | **1–21**, validated |

Builder **throws** if `recipients.length > 21`.

---

## 7. UX requirements

- Instruction: *"This opens your email app with a pre-written message. Review, add your name and address, then send."*
- Button shows recipient count (e.g. *"Opens your email app with 21 legislators in BCC."*)
- Message preview (subject + body) visible on page before click
- No in-app compose — handoff to native/Gmail client

---

## 8. Non-goals (v1)

- Server-side email send
- Send tracking
- Attachments / HTML body
- More than 21 recipients per campaign
- Copy-paste overflow blocks
- Semicolon BCC or client detection

---

## 9. Success criteria

| Criterion | Target |
|---|---|
| P1 client compatibility | Gmail web, Gmail iOS, Mail iOS |
| BCC integrity | All campaign recipients in compose |
| Formatting | Paragraphs, bullets, spaces, subject correct |
| Encoding | No literal `+` in subject/body on Gmail web |
| Validation | Campaigns > 21 recipients rejected at build time |

---

## 10. Launch checklist

- [x] URL builder uses `%20` encoding
- [x] Hard cap at 21 recipients (validation + PRD)
- [x] Unit tests pass
- [ ] Spot-check with real campaign on Gmail web + one iOS client
- [ ] Godfrey/Jason sign off on first live campaign copy

---

## 11. Appendix

See `mailto-stress-test/RESULTS.md` for full stress test matrix and encoding bug details.

| BCC count | Approx mailto length (`%20`) |
|---:|---:|
| 21 | ~2,300 |
