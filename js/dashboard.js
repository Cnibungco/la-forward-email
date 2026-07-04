(function () {
  var STORAGE_KEY = "laforward-dashboard-draft";

  var form = document.getElementById("campaign-form");
  var output = document.getElementById("output");
  var formError = document.getElementById("form-error");
  var shareUrlInput = document.getElementById("share-url");
  var copyStatus = document.getElementById("copy-status");

  function readFields() {
    return {
      title: document.getElementById("title").value.trim(),
      subject: document.getElementById("subject").value.trim(),
      body: document.getElementById("body").value,
      recipients: parseRecipients(document.getElementById("recipients").value),
      ctaLabel: document.getElementById("cta-label").value.trim() || "Email your representatives",
    };
  }

  function showError(message) {
    formError.textContent = message;
    formError.classList.remove("hidden");
    output.classList.add("hidden");
  }

  function clearError() {
    formError.classList.add("hidden");
    formError.textContent = "";
  }

  function saveDraft() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(readFields()));
    } catch (e) {
      // Private browsing or storage full — ignore.
    }
  }

  function loadDraft() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      applyCampaign(JSON.parse(raw));
    } catch (e) {
      // Corrupt draft — ignore.
    }
  }

  function applyCampaign(campaign) {
    document.getElementById("title").value = campaign.title || "";
    document.getElementById("subject").value = campaign.subject || "";
    document.getElementById("body").value = campaign.body || "";
    document.getElementById("recipients").value = (campaign.recipients || []).join("\n");
    document.getElementById("cta-label").value =
      campaign.ctaLabel && campaign.ctaLabel !== "Email your representatives"
        ? campaign.ctaLabel
        : "";
  }

  function loadExample() {
    clearError();
    if (window.EXAMPLE_CAMPAIGN) {
      applyCampaign(window.EXAMPLE_CAMPAIGN);
      saveDraft();
      return;
    }
    fetch("campaigns/ab123.json")
      .then(function (response) {
        if (!response.ok) throw new Error("not found");
        return response.json();
      })
      .then(function (campaign) {
        applyCampaign(campaign);
        saveDraft();
      })
      .catch(function () {
        showError("Could not load example campaign.");
      });
  }

  form.addEventListener("input", saveDraft);

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    clearError();

    var campaign = readFields();
    try {
      buildMailtoUrl(campaign);
    } catch (err) {
      showError(err.message);
      return;
    }

    var encoded = encodeCampaign(campaign);
    var url = buildShareUrl(encoded);

    shareUrlInput.value = url;
    document.getElementById("preview-link").href = url;
    output.classList.remove("hidden");
    copyStatus.textContent = "";
    output.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });

  document.getElementById("copy-link").addEventListener("click", function () {
    var url = shareUrlInput.value;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(
        function () { copyStatus.textContent = "Copied!"; },
        function () { fallbackCopy(url); }
      );
    } else {
      fallbackCopy(url);
    }
  });

  function fallbackCopy(url) {
    shareUrlInput.focus();
    shareUrlInput.select();
    copyStatus.textContent = "Select the link and copy manually (Cmd+C).";
  }

  document.getElementById("load-example").addEventListener("click", loadExample);

  document.getElementById("test-mailto").addEventListener("click", function () {
    clearError();
    try {
      window.location.href = buildMailtoUrl(readFields());
    } catch (err) {
      showError(err.message);
    }
  });

  loadDraft();
})();
