import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/worklog/realignment/audit_assets");
const BASE = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const PREFIX = "24_product_system_total_ui_ux_refresh";
const LETTERS = "TPL-VOLUMETRIC-LETTERS_v2";

async function main() {
  await mkdir(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
  await page.goto(`${BASE}/product-system/products/${LETTERS}`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await page.getByTestId("product-system-template-story").waitFor({ timeout: 30_000 });
  // Neutralize nested scroll clipping so the full story is captured in one shot.
  await page.addStyleTag({
    content: `
      [data-testid="product-system-detail-panel"],
      .xl\\:max-h-\\[calc\\(100vh-148px\\)\\],
      .xl\\:max-h-\\[calc\\(100vh-132px\\)\\] {
        max-height: none !important;
        overflow: visible !important;
        position: static !important;
      }
    `,
  });
  await page.waitForTimeout(700);
  await page.screenshot({
    path: path.join(OUT, `${PREFIX}_template_detail_story_element.png`),
    fullPage: true,
  });
  console.log("saved element story");
  await browser.close();
}
main().catch((e) => {
  console.error(e);
  process.exit(1);
});
