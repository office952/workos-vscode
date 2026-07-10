import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/intake-v6-step3-consolidated-status-v1/screenshots",
);
const ROUTE =
  "http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator";
const WORKSPACE = "22ef834d-f2d0-453b-a7a7-118928c98a39";

async function shot(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", file);
}

async function gotoStep(page, stepId) {
  const tab = page.getByTestId(`intake-v6-progress-step-${stepId}`);
  if (await tab.count()) {
    await tab.click();
    await page.waitForTimeout(900);
  }
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(ROUTE, { waitUntil: "networkidle", timeout: 120000 });
  await gotoStep(page, "confirm");

  await page.waitForSelector('[data-testid="intake-v6-step-confirm"]', { timeout: 60000 }).catch(() => {
    console.warn("confirm step not found");
  });

  const consolidated = page.getByTestId("intake-v6-confirm-consolidated-status");
  if (await consolidated.count()) {
    await consolidated.scrollIntoViewIfNeeded();
  }
  await shot(page, "02_step3_consolidated_status_default");

  const tier = await consolidated.getAttribute("data-status-tier");
  if (tier === "blocked") {
    await shot(page, "03_step3_blocked_state");
  } else if (tier === "attention") {
    await shot(page, "04_step3_attention_state");
    console.warn("blocked state not on fixture — captured attention as 04");
  } else if (tier === "ready") {
    await shot(page, "05_step3_ready_state");
  } else {
    console.warn(`ready/blocked/attention states depend on fixture — tier=${tier}`);
  }

  const modular = page.getByTestId("intake-v6-modular-form-awareness");
  if (await modular.count()) {
    await modular.scrollIntoViewIfNeeded();
  }
  await shot(page, "06_step3_tabs_reduced_noise");

  const footer = page.getByTestId("intake-v6-operator-workspace-footer");
  if (await footer.count()) {
    await footer.scrollIntoViewIfNeeded();
  }
  await shot(page, "07_step3_footer_scope_regression");

  await gotoStep(page, "review");
  await page.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 }).catch(() => {});
  const calc = page.getByTestId("intake-v6-review-calculator-panel");
  if (await calc.count()) {
    await calc.scrollIntoViewIfNeeded();
  }
  await shot(page, "08_step2_live_calculation_regression");

  const diagnostic = page.getByTestId("intake-v6-review-technical-details");
  if (await diagnostic.count()) {
    await diagnostic.scrollIntoViewIfNeeded();
    await shot(page, "09_step2_diagnostic_regression");
  }

  await gotoStep(page, "layers");
  await page.waitForTimeout(800);
  await shot(page, "10_step1_badge_noise_regression");

  console.log(
    JSON.stringify(
      {
        url: ROUTE,
        workspace: WORKSPACE,
        confirmTier: tier,
        notes: "01 before not captured pre-implementation",
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
