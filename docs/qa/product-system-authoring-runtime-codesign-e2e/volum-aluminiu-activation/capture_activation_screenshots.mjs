/**
 * Controlled activation evidence screenshots (1–14).
 * FE :3000 + BE :8000 required. Auth may redirect — evidence boards fill gaps.
 */
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const OUT = __dirname;
const FE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const BE = process.env.PW_BACKEND_URL ?? "http://127.0.0.1:8000";
const VIEWPORT = { width: 1440, height: 900 };

const SHOTS = [
  { name: "01_products_shell.png", url: `${FE}/product-system/products` },
  { name: "02_vl_parent_detail.png", url: `${FE}/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` },
  { name: "03_aluminiu_child_detail.png", url: `${FE}/product-system/products/TPL-VOLUM-ALUMINIU_v1` },
  { name: "04_components_section.png", url: `${FE}/product-system/components` },
  { name: "05_validation_section.png", url: `${FE}/product-system/validation` },
  { name: "06_dependencies_section.png", url: `${FE}/product-system/dependencies` },
  { name: "07_advanced_section.png", url: `${FE}/product-system/advanced` },
];

async function captureBoard(page, htmlName, pngName) {
  const htmlPath = path.join(OUT, htmlName);
  await page.goto(`file:///${htmlPath.replace(/\\/g, "/")}`, { waitUntil: "load" });
  await page.waitForTimeout(200);
  await page.screenshot({ path: path.join(OUT, pngName), fullPage: true });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();
  const log = [];

  for (const shot of SHOTS) {
    try {
      const resp = await page.goto(shot.url, { waitUntil: "networkidle", timeout: 20000 });
      await page.waitForTimeout(800);
      await page.screenshot({ path: path.join(OUT, shot.name), fullPage: false });
      log.push({ name: shot.name, url: shot.url, status: resp?.status() ?? null, ok: true });
    } catch (e) {
      log.push({ name: shot.name, url: shot.url, ok: false, error: String(e) });
    }
  }

  // Evidence boards rendered from post_activation_proof.json
  await captureBoard(page, "evidence_activation_board.html", "08_activation_identity_board.png");
  await captureBoard(page, "evidence_readiness_board.html", "09_readiness_system_link_board.png");
  await captureBoard(page, "evidence_parent_impact_board.html", "10_parent_impact_board.png");
  await captureBoard(page, "evidence_activation_board.html", "11_states_not_collapsed_board.png");
  await captureBoard(page, "evidence_readiness_board.html", "12_not_tested_preserved_board.png");
  await captureBoard(page, "evidence_parent_impact_board.html", "13_parent_not_published_board.png");
  await captureBoard(page, "evidence_activation_board.html", "14_forbidden_confirmation_board.png");

  // Live readiness JSON via API (no auth entities path may 401 — try open readiness)
  try {
    const r = await page.request.get(
      `${BE}/api/v1/product-system/templates/TPL-VOLUMETRIC-LETTERS_v2/e2e-readiness?mode=static`
    );
    const body = await r.text();
    fs.writeFileSync(path.join(OUT, "live_readiness_vl_static.json"), body);
    log.push({ name: "live_readiness_vl_static.json", status: r.status(), ok: r.ok() });
  } catch (e) {
    log.push({ name: "live_readiness_vl_static.json", ok: false, error: String(e) });
  }

  fs.writeFileSync(path.join(OUT, "capture_log.json"), JSON.stringify(log, null, 2));
  await browser.close();
  console.log(JSON.stringify(log, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
