import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/intake-v6-live-calculation-balance-v1/screenshots",
);
const ROUTE =
  "http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator";
const WORKSPACE = "22ef834d-f2d0-453b-a7a7-118928c98a39";

async function shot(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", file);
}

async function gotoReviewStep(page) {
  await page.goto(ROUTE, { waitUntil: "networkidle", timeout: 120000 });
  const reviewTab = page.getByTestId("intake-v6-progress-step-review");
  if (await reviewTab.count()) {
    await reviewTab.click();
    await page.waitForTimeout(800);
  }
  await page.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 }).catch(() => {
    console.warn("review step marker not found");
  });
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await gotoReviewStep(page);

  const calcPanel = page.getByTestId("intake-v6-review-calculator-panel");
  if (await calcPanel.count()) {
    await calcPanel.scrollIntoViewIfNeeded();
  }
  await shot(page, "02_step2_live_calculation_balanced_default");

  const blockerBanner = page.getByTestId("intake-v6-review-operator-blocker-banner");
  if (await blockerBanner.count()) {
    await shot(page, "03_step2_live_calculation_with_blocker");
  } else {
    console.warn("blocker banner not visible — skipping 03");
  }

  const detailsBtn = page.getByTestId("intake-v6-review-calculator-details");
  if (await detailsBtn.count()) {
    await detailsBtn.click();
    await page.waitForTimeout(500);
    await shot(page, "04_step2_live_calculation_subtotals");
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);
  }

  const diagnostic = page.getByTestId("intake-v6-review-technical-details");
  if (await diagnostic.count()) {
    await diagnostic.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    await shot(page, "06_step2_diagnostic_collapsed_regression");
  } else {
    console.warn("diagnostic section not found — skipping 06");
  }

  const estimateUnavailable = page.getByTestId("intake-v6-live-estimate-unavailable");
  if (await estimateUnavailable.count()) {
    await shot(page, "05_step2_live_calculation_incomplete_state");
  } else {
    console.warn("incomplete estimate state not available on fixture — skipping 05");
  }

  await page.getByTestId("intake-v6-review-tab-iluminare").click().catch(() => {});
  await page.waitForTimeout(500);
  if (await calcPanel.count()) {
    await calcPanel.scrollIntoViewIfNeeded();
  }
  await shot(page, "07_step2_iluminare_regression");

  const layersTab = page.getByTestId("intake-v6-progress-step-layers");
  if (await layersTab.count()) {
    await layersTab.click();
    await page.waitForTimeout(800);
    await shot(page, "08_step1_badge_noise_regression");
  }

  const confirmTab = page.getByTestId("intake-v6-progress-step-confirm");
  if (await confirmTab.count()) {
    await confirmTab.click();
    await page.waitForTimeout(800);
    await shot(page, "09_step3_no_intentional_changes");
  }

  console.log(
    JSON.stringify(
      {
        url: ROUTE,
        workspace: WORKSPACE,
        step: "review",
        notes: "01 before state not captured post-implementation; incomplete state depends on fixture",
      },
      null,
      2,
    ),
  );

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
