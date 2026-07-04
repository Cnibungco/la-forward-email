/**
 * Encode/decode campaign data in shareable URL hashes.
 */
(function (root) {
  function encodeCampaign(campaign) {
    var payload = JSON.stringify({
      t: campaign.title || "",
      s: campaign.subject,
      b: campaign.body,
      r: campaign.recipients,
      c: campaign.ctaLabel || "",
    });
    return btoa(unescape(encodeURIComponent(payload)))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");
  }

  function decodeCampaign(encoded) {
    if (!encoded) {
      throw new Error("No campaign data in link.");
    }

    var base64 = encoded.replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4) {
      base64 += "=";
    }

    var data;
    try {
      data = JSON.parse(decodeURIComponent(escape(atob(base64))));
    } catch (e) {
      throw new Error("Could not read campaign data. The link may be corrupted.");
    }

    if (!data.s || !data.b || !Array.isArray(data.r) || data.r.length === 0) {
      throw new Error("Invalid campaign data in link.");
    }

    return {
      title: data.t || "Email your representatives",
      subject: String(data.s),
      body: String(data.b),
      recipients: data.r,
      ctaLabel: data.c || "Email your representatives",
    };
  }

  function parseRecipients(text) {
    return text
      .split(/[\n,;]+/)
      .map(function (s) { return s.trim(); })
      .filter(Boolean);
  }

  function buildShareUrl(encoded) {
    var url = new URL("email.html", window.location.href);
    url.hash = encoded;
    return url.href;
  }

  root.encodeCampaign = encodeCampaign;
  root.decodeCampaign = decodeCampaign;
  root.parseRecipients = parseRecipients;
  root.buildShareUrl = buildShareUrl;
})(typeof globalThis !== "undefined" ? globalThis : typeof window !== "undefined" ? window : global);
