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
    var json = decodeURIComponent(escape(atob(base64)));
    var data = JSON.parse(json);
    return {
      title: data.t || "Email your representatives",
      subject: data.s,
      body: data.b,
      recipients: data.r,
      ctaLabel: data.c || "Email your representatives",
    };
  }

  function parseRecipients(text) {
    return text
      .split(/[\n,;]+/)
      .map(function (s) {
        return s.trim();
      })
      .filter(Boolean);
  }

  function shareUrl(encoded) {
    var base = window.location.href.replace(/[#?].*$/, "").replace(/[^/]*$/, "");
    return base + "email.html#" + encoded;
  }

  root.encodeCampaign = encodeCampaign;
  root.decodeCampaign = decodeCampaign;
  root.parseRecipients = parseRecipients;
  root.buildShareUrl = shareUrl;
})(typeof globalThis !== "undefined" ? globalThis : typeof window !== "undefined" ? window : global);
