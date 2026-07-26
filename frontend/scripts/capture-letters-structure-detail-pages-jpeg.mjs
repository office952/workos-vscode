/**
 * Capture Letters structure detail pages (Vizual față + Volum aluminiu) as JPEG.
 * Requires FE :3000 (+ session / Dev Auth as usual).
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/worklog/realignment/audit_assets");
const BASE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const TPL = encodeURIComponent("TPL-VOLUMETRIC-LETTERS_v2");

async function shotJpeg(page, name, { fullPage = true } = {}) {
  await mkdir(OUT, { recursive: true });
  const file = path.join(OUT, `${name}.jpg`);
  await page.screenshot({
    path: file,
    fullPage,
    type: "jpeg",
    quality: 90,
  });
  console.log("saved", file);
}

async function waitReady(page, testId) {
  await page.getByTestId(testId).waitFor({ timeout: 60_000 });
  await page.waitForTimeout(600);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });

  // Product detail — structure list (thin teasers for face + volume)
  await page.goto(`${BASE}/product-system/products/${TPL}`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await page.waitForTimeout(2000);
  const structureTab = page.getByTestId("product-system-template-detail-tab-structure");
  if ((await structureTab.count()) > 0) {
    await structureTab.click();
    await page.waitForTimeout(800);
  }
  // Fallback: some shells use dossier / editor structure
  const openEditor = page.getByTestId("product-system-template-detail-open-editor");
  if ((await openEditor.count()) > 0 && (await page.getByTestId("product-system-v2-structure-row-0").count()) === 0) {
    await openEditor.click();
    await page.waitForTimeout(800);
  }
  if ((await page.getByTestId("product-system-v2-structure-row-0").count()) > 0) {
    await shotJpeg(page, "24_letters_structure_list_face_volume_teasers", { fullPage: false });
  } else {
    console.warn("structure list not found — skipping list shot");
  }

  await page.goto(`${BASE}/product-system/products/${TPL}/structure/vizual-fata`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await waitReady(page, "letters-face-structure-detail");
  await shotJpeg(page, "24_letters_vizual_fata_structure_detail_full");
  await shotJpeg(page, "24_letters_vizual_fata_structure_detail_viewport", { fullPage: false });

  await page.goto(`${BASE}/product-system/products/${TPL}/structure/volum-aluminiu`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await waitReady(page, "letters-volume-structure-detail");
  await shotJpeg(page, "24_letters_volum_aluminiu_structure_detail_full");
  await shotJpeg(page, "24_letters_volum_aluminiu_structure_detail_viewport", { fullPage: false });

  await page.goto(`${BASE}/product-system/products/${TPL}/structure/capac-spate`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await waitReady(page, "letters-back-structure-detail");
  await shotJpeg(page, "24_letters_capac_spate_structure_detail_full");
  await shotJpeg(page, "24_letters_capac_spate_structure_detail_viewport", { fullPage: false });

  await page.goto(`${BASE}/product-system/products/${TPL}/structure/sistem-led`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await waitReady(page, "letters-led-structure-detail");
  await shotJpeg(page, "24_letters_sistem_led_structure_detail_full");
  await shotJpeg(page, "24_letters_sistem_led_structure_detail_viewport", { fullPage: false });

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
