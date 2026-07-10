import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/screenshots/2026-07-10_intake_v6_backing_order_fix",
);
const ROUTE =
  "http://127.0.0.1:3000/intake-v6/633b5663-8d15-4dca-805f-4cca202323f6/operator";

async function shot(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", file);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(ROUTE, { waitUntil: "networkidle", timeout: 120000 });

  await page.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 }).catch(() => {
    console.warn("review step not found — workspace may need review tab active");
  });

  const reviewTab = page.getByTestId("intake-v6-wizard-step-review");
  if (await reviewTab.count()) {
    await reviewTab.click();
    await page.waitForTimeout(500);
  }

  const backing = page.getByTestId("intake-v6-review-section-backing");
  await backing.scrollIntoViewIfNeeded();
  await shot(page, "01_backing_after_composition");

  const composition = page.getByTestId("intake-v6-product-composition-panel").first();
  const tabs = page.getByTestId("intake-v6-review-tabs");
  const backingBox = await backing.boundingBox();
  const compositionBox = await composition.boundingBox().catch(() => null);
  const tabsBox = await tabs.boundingBox().catch(() => null);

  await page.getByTestId("intake-v6-review-tab-iluminare").click().catch(() => {});
  await page.waitForTimeout(400);
  await backing.scrollIntoViewIfNeeded();
  await shot(page, "02_backing_before_led");

  const ledSection = page.getByTestId("intake-v6-review-section-lighting");
  if (await ledSection.count()) {
    await ledSection.scrollIntoViewIfNeeded();
  }

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
  await backing.scrollIntoViewIfNeeded();
  await shot(page, "03_led_off_backing_still_visible");

  const backingVisible = await backing.isVisible();
  const checks = {
    backingVisible,
    backingAfterComposition:
      compositionBox && backingBox ? backingBox.y >= compositionBox.y : null,
    backingBeforeTabs: backingBox && tabsBox ? backingBox.y < tabsBox.y : null,
    backingSectionTestId: (await backing.count()) > 0,
    backingSelect: (await page.getByTestId("intake-v6-backing-mode").count()) > 0,
  };
  console.log("checks", JSON.stringify(checks, null, 2));

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
