/**
 * OFERTA_VS_COST_INTERN_INTAKE_CHROME_V1 — runtime screenshots (labels/IA only).
 * Requires FE :3000 + BE :8000 with Dev Auth.
 */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/worklog/realignment/audit_assets");
const BASE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";

async function shot(page, name) {
  await mkdir(OUT, { recursive: true });
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", file);
}

async function enableDevMode(page) {
  // Dev Mode toggle lives in shell chrome; try common selectors without failing the capture.
  const candidates = [
    page.getByTestId("dev-mode-toggle"),
    page.getByRole("button", { name: /dev mode/i }),
    page.getByRole("switch", { name: /dev mode/i }),
    page.locator('[data-testid*="dev-mode"]'),
  ];
  for (const locator of candidates) {
    try {
      if ((await locator.count()) > 0) {
        const el = locator.first();
        const pressed = await el.getAttribute("aria-pressed");
        const checked = await el.getAttribute("aria-checked");
        if (pressed === "true" || checked === "true") return;
        await el.click({ timeout: 2000 }).catch(() => {});
        return;
      }
    } catch {
      // continue
    }
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(`${BASE}/intake`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1200);
  await enableDevMode(page);
  await shot(page, "22_oferta_vs_cost_intern_intake");

  await page.goto(`${BASE}/intake-v6/operator`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1500);
  await shot(page, "22_oferta_vs_cost_intern_intake_v6_operator");

  await page.goto(`${BASE}/quotes`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1500);
  await shot(page, "22_oferta_vs_cost_intern_quotes");

  await page.goto(`${BASE}/product-system/products`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  try {
    await page.getByTestId("product-system-unified-catalog").waitFor({ timeout: 60_000 });
  } catch {
    await page.waitForTimeout(2000);
  }
  await shot(page, "22_oferta_vs_cost_intern_product_system_products");

  await page.goto(`${BASE}/product-system/products/TPL-VOLUMETRIC-LETTERS_v2`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await page.waitForTimeout(1500);
  await shot(page, "22_oferta_vs_cost_intern_product_template_letters");

  await page.goto(`${BASE}/inventory/pricing`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1500);
  await shot(page, "22_oferta_vs_cost_intern_pricing_registry");

  await page.goto(`${BASE}/utilaje`, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForTimeout(1200);
  await shot(page, "22_oferta_vs_cost_intern_utilaje_registry");

  await browser.close();
  console.log("done");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
