(function () {
  var titleEl = document.getElementById("campaign-title");
  var instructionsEl = document.getElementById("instructions-text");
  var actionSection = document.getElementById("action-section");
  var previewSection = document.getElementById("preview-section");

  function showError(title, message) {
    document.title = "LA Forward — " + title;
    titleEl.textContent = title;
    instructionsEl.textContent = message;
    actionSection.hidden = true;
    previewSection.hidden = true;
  }

  var hash = window.location.hash.slice(1);
  if (!hash) {
    showError(
      "Campaign not found",
      "This link is missing campaign data. Ask LA Forward for a valid link."
    );
    return;
  }

  var campaign;
  try {
    campaign = decodeCampaign(hash);
    buildMailtoUrl(campaign);
  } catch (err) {
    showError("Invalid campaign link", err.message);
    return;
  }

  var mailtoUrl = buildMailtoUrl(campaign);
  var count = campaign.recipients.length;

  document.title = "LA Forward — " + campaign.title;
  titleEl.textContent = campaign.title;
  document.getElementById("email-cta").textContent = campaign.ctaLabel;
  document.getElementById("email-cta").href = mailtoUrl;
  document.getElementById("recipient-note").textContent =
    "Opens your email app with " + count + " legislator" + (count === 1 ? "" : "s") + " in BCC.";
  document.getElementById("preview-subject").textContent = campaign.subject;
  document.getElementById("preview-body").textContent = campaign.body;
})();
