#!/usr/bin/env node
import { writeFileSync } from "fs";
import { SUBJECT, BCC_ADDRESSES, BODY } from "./campaign.js";

function buildMailto({ bccSeparator }) {
  const bcc = BCC_ADDRESSES.join(bccSeparator);
  const params = new URLSearchParams();
  params.set("bcc", bcc);
  params.set("subject", SUBJECT);
  params.set("body", BODY);
  return `mailto:?${params.toString()}`;
}

function analyze(label, url) {
  const bccParam = new URL(url).searchParams.get("bcc") ?? "";
  const parsed = bccParam.split(/[,;]/).filter(Boolean);
  return {
    label,
    totalLength: url.length,
    bccSeparator: label.includes("comma") ? "," : ";",
    bccCountInUrl: parsed.length,
    subjectLength: SUBJECT.length,
    bodyLength: BODY.length,
    url,
  };
}

const comma = analyze("comma-separated BCC", buildMailto({ bccSeparator: "," }));
const semicolon = analyze("semicolon-separated BCC", buildMailto({ bccSeparator: ";" }));

const report = {
  generatedAt: new Date().toISOString(),
  subject: SUBJECT,
  expectedBccCount: BCC_ADDRESSES.length,
  versions: [comma, semicolon],
};

writeFileSync("mailto-urls.json", JSON.stringify(report, null, 2));

console.log("=== LA Forward Mailto Stress Test URLs ===\n");
for (const v of [comma, semicolon]) {
  console.log(`${v.label}`);
  console.log(`  Total URL length: ${v.totalLength} chars`);
  console.log(`  BCC addresses encoded: ${v.bccCountInUrl}`);
  console.log(`  Subject length: ${v.subjectLength} chars`);
  console.log(`  Body length: ${v.bodyLength} chars`);
  console.log(`  URL preview (first 120): ${v.url.slice(0, 120)}...`);
  console.log();
}

console.log("Full URLs written to mailto-urls.json");
