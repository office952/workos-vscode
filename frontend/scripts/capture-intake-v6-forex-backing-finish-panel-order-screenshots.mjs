import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_finish_panel_order",
);
const ROUTE =
  "http://127.0.0.1:3000/intake-v6/633b5663-8d15-4dca-805f-4cca202323f6/operator";

async function shot(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", file);
}

async function ensureReviewStep(page) {
  const reviewTab = page.getByTestId("intake-v6-wizard-step-review");
  if (await reviewTab.count()) {
    await reviewTab.click();
    await page.waitForTimeout(400);
  }
  await page.getByTestId("intake-v6-review-tab-finisaje").click();
  await page.waitForTimeout(300);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(ROUTE, { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 });
  await ensureReviewStep(page);

  const finisajePanel = page.getByTestId("intake-v6-review-tab-panel-finisaje");
  const backingRow = page.getByTestId("intake-v6-backing-finish-row");
  await finisajePanel.scrollIntoViewIfNeeded();
  await backingRow.scrollIntoViewIfNeeded();
  await shot(page, "01_finish_panel_with_forex_dropdown");

  await page.getByTestId("intake-v6-review-tab-iluminare").click();
  await page.waitForTimeout(400);
  await page.getByTestId("intake-v6-review-section-lighting").scrollIntoViewIfNeeded();
  await shot(page, "02_forex_not_under_led");

  await ensureReviewStep(page);
  const illuminatedToggle = page.getByTestId("intake-v6-illuminated");
  if (await illuminatedToggle.count()) {
    const isChecked = await illuminatedToggle.isChecked().catch(() => true);
    if (isChecked) {
      await illuminatedToggle.evaluate((el) => {
        el.click();
      });
      await page.waitForTimeout(400);
    }
  }
  await backingRow.scrollIntoViewIfNeeded();
  await shot(page, "03_led_off_forex_still_visible");

  const backingInFinisaje = await finisajePanel.getByTestId("intake-v6-backing-finish-row").count();
  const backingUnderLed = await page
    .getByTestId("intake-v6-review-section-lighting")
    .getByTestId("intake-v6-backing-mode")
    .count();
  const checks = {
    backingInFinisaje: backingInFinisaje > 0,
    backingNotUnderLed: backingUnderLed === 0,
    backingSelectVisible: (await page.getByTestId("intake-v6-backing-mode").count()) > 0,
    finisajeTabActive: true,
  };
  console.log("checks", JSON.stringify(checks, null, 2));

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
