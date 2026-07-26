/**
 * UI evidence — WORKOS_ACM_PANEL_NAMING_OWNERSHIP_ASSEMBLY_AND_INVENTORY_BINDING_V1
 * Fixture IV6-DB2F86B7 — Blueprint L1-P assembly 2000×350 still visible (no regression).
 */
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const ID = "a7b0162b-dc91-467f-aa24-c1279fb3a073";
const OUT = __dirname;

async function main() {
  const shots = path.join(OUT, "shots");
  fs.mkdirSync(shots, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await ctx.newPage();

  await page.goto(`${UI}/intake-v6/${ID}/operator`, {
    waitUntil: "domcontentloaded",
    timeout: 120000,
  });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 60000 });

  await page.getByTestId("intake-v6-product-component-row-acm_panel").click();
  await page.waitForTimeout(400);

  const preview = page.getByTestId("intake-v6-acm-blueprint-preview");
  await preview.waitFor({ state: "visible", timeout: 15000 });
  await page.getByTestId("intake-v6-acm-blueprint-toggle").click();
  await page.waitForTimeout(300);

  const svg = page.getByTestId("intake-v6-acm-blueprint-front-svg");
  await svg.waitFor({ state: "visible", timeout: 5000 });
  const aw = await svg.getAttribute("data-assembly-width");
  const ah = await svg.getAttribute("data-assembly-height");
  const overall = await page
    .getByTestId("intake-v6-acm-blueprint-overall-label")
    .evaluate((el) => el.textContent?.trim() ?? "");

  await page.screenshot({ path: path.join(shots, "01-blueprint-assembly-2000x350.png") });
  await page.screenshot({
    path: path.join(shots, "02-configurare-full.png"),
    fullPage: true,
  });

  const proof = {
    ok: aw === "2000" && ah === "350",
    assembly_width: aw,
    assembly_height: ah,
    overall_label: overall,
    ui: UI,
    workspace_id: ID,
  };
  fs.writeFileSync(path.join(OUT, "ui-proof.json"), JSON.stringify(proof, null, 2));
  console.log(proof.ok ? "PASS" : "FAIL", JSON.stringify(proof));
  await browser.close();
  process.exit(proof.ok ? 0 : 1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
