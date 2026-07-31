/**
 * Capacity Batch 17 — ops-graph before/after screenshots (GET-only).
 * Usage: node capture-ops-graph.mjs before|after
 */
import path from "path";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");

const phase = process.argv[2] === "after" ? "after" : "before";
const OUT = path.join(__dirname, "screenshots");
const URL = "http://127.0.0.1:3000/execution/ops-graph";

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
} finally {
  await browser.close();
}
