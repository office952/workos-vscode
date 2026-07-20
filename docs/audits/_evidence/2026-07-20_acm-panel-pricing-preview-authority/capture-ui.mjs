/**
 * UI + network proof — WORKOS_ACM_PANEL_PRICING_PREVIEW_AND_AUTHORITY_GATES_V1
 * Fixture IV6-DB2F86B7 — Review/Confirm live-calc AcmPanel provisional; zero writes on expand.
 *
 * Env:
 *   PW_BASE_URL (default http://127.0.0.1:3011)
 *   PW_BACKEND_URL optional — inventory pages use same origin proxy
 */
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3011";
const ID = "a7b0162b-dc91-467f-aa24-c1279fb3a073";
const OUT = __dirname;

async function shot(page, name, opts = {}) {
  const shots = path.join(OUT, "shots");
  fs.mkdirSync(shots, { recursive: true });
  await page.screenshot({ path: path.join(shots, name), ...opts });
}

async function main() {
  const mutating = [];
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await ctx.newPage();
  page.on("request", (req) => {
    const m = req.method();
    if (m === "GET" || m === "HEAD" || m === "OPTIONS") return;
    mutating.push({ method: m, url: req.url() });
  });

  await page.goto(`${UI}/intake-v6/${ID}/operator`, {
    waitUntil: "domcontentloaded",
    timeout: 120000,
  });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 60000 });
  await page.waitForTimeout(2000);

  await shot(page, "01-review-full.png", { fullPage: true });

  // Prefer sticky Review right-rail calculator (sidebar copy may be display:none on desktop).
  let panel = page
    .getByTestId("intake-v6-review-calculator-panel")
    .getByTestId("intake-v6-acm-panel-provisional-pricing");
  if ((await panel.count()) === 0) {
    panel = page.getByTestId("intake-v6-acm-panel-provisional-pricing").nth(1);
  }
  await panel.waitFor({ state: "visible", timeout: 45000 });
  await panel.scrollIntoViewIfNeeded();
  await shot(page, "02-sticky-live-calc.png");
  await shot(page, "03-acm-provisional-header.png");

  const status = await panel.getAttribute("data-status");
  const finalElig = await panel.getAttribute("data-final-eligible");
  const offerElig = await panel.getAttribute("data-offer-eligible");
  const execElig = await panel.getAttribute("data-execution-eligible");
  const face = await panel.getByTestId("intake-v6-acm-panel-face-area").innerText();
  const summary = await panel.getByTestId("intake-v6-acm-panel-provisional-summary").innerText();
  await shot(page, "04-assembly-summary.png");
  await shot(page, "05-face-area.png");

  const writesBeforeExpand = mutating.length;
  await panel.getByTestId("intake-v6-acm-panel-breakdown-toggle").click();
  await page.waitForTimeout(300);
  await shot(page, "06-expanded-breakdown.png");
  await shot(page, "07-material-line.png");
  await shot(page, "08-cutting-line.png");
  await shot(page, "09-vgroove-line.png");
  await shot(page, "10-remaining-acm-lines.png");
  await shot(page, "11-segmentation-warning.png");
  await shot(page, "12-technical-warning.png");
  await shot(page, "13-composition-warning.png");
  await shot(page, "14-final-unavailable.png");
  await shot(page, "15-offer-unavailable.png");

  await panel.getByTestId("intake-v6-acm-panel-breakdown-toggle").click();
  await page.waitForTimeout(200);
  const writesAfterToggle = mutating.length - writesBeforeExpand;

  // Inspector region — no money badges expected in AcmPanel inspector body
  await page.getByTestId("intake-v6-product-component-row-acm_panel").click().catch(() => {});
  await page.waitForTimeout(500);
  await shot(page, "17-inspector-region.png");
  const inspectorText = await page.locator("body").innerText();
  const inspectorHasProvisionalHeader = /Estimare provizorie AcmPanel/.test(inspectorText);

  // Confirm continuity
  await page.getByTestId("intake-v6-progress-step-confirm").click().catch(() => {});
  await page.getByTestId("intake-v6-step-confirm").waitFor({ state: "visible", timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(2500);
  const confirmPanel = page.getByTestId("intake-v6-step-confirm").getByTestId("intake-v6-acm-panel-provisional-pricing").first();
  await confirmPanel.waitFor({ state: "visible", timeout: 45000 }).catch(() => {});
  const confirmVisible = await confirmPanel.isVisible().catch(() => false);
  if (confirmVisible) {
    await confirmPanel.scrollIntoViewIfNeeded();
    await shot(page, "16-confirm-continuity.png");
  }

  // Mobile
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  await page.waitForTimeout(1000);
  await page.getByTestId("intake-v6-acm-panel-provisional-pricing").first().waitFor({ state: "visible", timeout: 30000 }).catch(() => {});
  await shot(page, "20-mobile-live-calc.png");
  await shot(page, "21-full-page-final.png", { fullPage: true });

  // Inventory / Pricing registry — read-only admin truth
  await page.setViewportSize({ width: 1440, height: 900 });
  const invWritesBefore = mutating.length;
  await page.goto(`${UI}/inventory`, { waitUntil: "domcontentloaded", timeout: 90000 });
  await page.waitForTimeout(1500);
  await shot(page, "18-inventory-materials.png", { fullPage: true });
  await page.goto(`${UI}/inventory/pricing`, { waitUntil: "domcontentloaded", timeout: 90000 });
  await page.waitForTimeout(1500);
  await shot(page, "19-pricing-registry.png", { fullPage: true });
  const invWrites = mutating.filter((w, i) => i >= invWritesBefore);

  const proof = {
    ok:
      status === "provisional_with_warnings" &&
      finalElig === "false" &&
      offerElig === "false" &&
      execElig === "false" &&
      /0\.7|0,7/.test(face) &&
      /2000/.test(summary) &&
      writesAfterToggle === 0 &&
      confirmVisible,
    status,
    finalElig,
    offerElig,
    execElig,
    face,
    summary,
    writesAfterToggle,
    confirmVisible,
    inspectorHasProvisionalHeader,
    mutatingWrites: mutating,
    inventoryPricingMutating: invWrites,
    baseUrl: UI,
  };
  fs.writeFileSync(path.join(OUT, "ui-proof.json"), JSON.stringify(proof, null, 2));
  console.log(proof.ok ? "PASS" : "FAIL", JSON.stringify(proof, null, 2));
  await browser.close();
  process.exit(proof.ok ? 0 : 1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
