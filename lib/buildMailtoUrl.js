/**
 * Build a mailto URL for LA Forward one-click email campaigns.
 * Spaces must be %20, never + (Gmail web leaves + literal).
 */
(function (root) {
  var MAX_RECIPIENTS = 21;
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function assertCampaign(campaign) {
    var recipients = campaign.recipients;
    var subject = campaign.subject;
    var body = campaign.body;

    if (!Array.isArray(recipients) || recipients.length === 0) {
      throw new Error("Campaign must include at least one recipient.");
    }
    if (recipients.length > MAX_RECIPIENTS) {
      throw new Error(
        "Campaign has " + recipients.length + " recipients; maximum is " + MAX_RECIPIENTS + "."
      );
    }
    if (!subject || typeof subject !== "string" || !subject.trim()) {
      throw new Error("Campaign must include a subject.");
    }
    if (!body || typeof body !== "string" || !body.trim()) {
      throw new Error("Campaign must include a body.");
    }

    recipients.forEach(function (email, i) {
      if (typeof email !== "string" || !EMAIL_RE.test(email.trim())) {
        throw new Error("Invalid email at index " + i + ": " + email);
      }
    });
  }

  function buildMailtoUrl(campaign) {
    assertCampaign(campaign);
    var params = new URLSearchParams();
    params.set("bcc", campaign.recipients.map(function (e) { return e.trim(); }).join(","));
    params.set("subject", campaign.subject.trim());
    params.set("body", campaign.body);
    return "mailto:?" + params.toString().replace(/\+/g, "%20");
  }

  root.buildMailtoUrl = buildMailtoUrl;
  root.MAX_RECIPIENTS = MAX_RECIPIENTS;
})(typeof globalThis !== "undefined" ? globalThis : typeof window !== "undefined" ? window : global);
