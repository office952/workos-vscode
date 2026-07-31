/**
 * Capacity Batch 18 Track B — OR-07 narrow nav drawer before/after (GET-only).
 * Usage: node docs/qa/capacity-batch-18/capture-or-07.mjs before|after [baseUrl]
 * Default baseUrl: http://127.0.0.1:3000
 */
import path from "path";
import { createRequire } from "module";
import { fileURLToPath } from "url";
import fs from "fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");

const phase = process.argv[2] === "after" ? "after" : "before";
const baseUrl = process.argv[3] || "http://127.0.0.1:3000";
const OUT = path.join(__dirname, "screenshots", "or-07");
const URL = `${baseUrl.replace(/\/$/, "")}/execution/ops-graph`;

fs.mkdirSync(OUT, { recursive: true });

async function shot(page, name) {
  const file = path.join(OUT, `${phase}-${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log("wrote", file);
}

const browser = await chromium.launch({ headless: true });
try {
  const desktop = await browser.newContext({
    viewport: { width: 1440, height: 1100 },
  });
  const dPage = await desktop.newPage();
  await dPage.goto(URL, { waitUntil: "networkidle", timeout: 60000 });
  await dPage.waitForSelector('[data-testid="materialized-ops-graph-page"]', {
    timeout: 30000,
  });
  await dPage.waitForTimeout(800);
  await shot(dPage, "ops-graph-desktop");

  const narrow = await browser.newContext({
    viewport: { width: 390, height: 900 },
  });
  const nPage = await narrow.newPage();
  await nPage.goto(URL, { waitUntil: "networkidle", timeout: 60000 });
  await nPage.waitForSelector('[data-testid="materialized-ops-graph-page"]', {
    timeout: 30000,
  });
  await nPage.waitForTimeout(800);
  await shot(nPage, "ops-graph-narrow");
  await nPage
    .locator('[data-testid="materialized-ops-graph-page"]')
    .screenshot({
      path: path.join(OUT, `${phase}-ops-graph-narrow-content.png`),
    });
  console.log(
    "wrote",
    path.join(OUT, `${phase}-ops-graph-narrow-content.png`),
  );

  const openToggle = nPage.locator('[data-testid="workos-nav-drawer-toggle"]');
  if ((await openToggle.count()) > 0) {
    await openToggle.click({ force: true });
    await nPage.waitForTimeout(400);
    await shot(nPage, "ops-graph-narrow-drawer-open");
  }
} finally {
  await browser.close();
}
