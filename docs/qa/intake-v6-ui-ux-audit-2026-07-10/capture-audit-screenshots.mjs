/**
 * One-off audit capture script — Intake V6 Steps 1–3.
 * Run: node docs/qa/intake-v6-ui-ux-audit-2026-07-10/capture-audit-screenshots.mjs
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "screenshots");
fs.mkdirSync(OUT, { recursive: true });

const WORKSPACES = [
  "22ef834d-f2d0-453b-a7a7-118928c98a39",
  "IR-MR18L96M",
];

async function pickWorkspace(page) {
  for (const id of WORKSPACES) {
    const url = `http://127.0.0.1:3000/intake-v6/${id}/operator`;
    await page.goto(url, { waitUntil: "networkidle", timeout: 90_000 });
    await page.waitForTimeout(2500);
    const progress = page.getByTestId("intake-v6-progress");
    if ((await progress.count()) > 0) {
      return { id, url };
    }
  }
  throw new Error("No usable Intake V6 workspace found");
}

async function shot(page, name, meta) {
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  fs.appendFileSync(
    path.join(OUT, "capture_manifest.jsonl"),
    JSON.stringify({ file: `${name}.png`, ...meta }) + "\n",
  );
  console.log("saved", name);
}

async function gotoStep(page, stepId) {
  await page.getByTestId(`intake-v6-progress-step-${stepId}`).click();
  await page.waitForTimeout(800);
}

async function expandIfPresent(page, testId) {
  const el = page.getByTestId(testId);
  if ((await el.count()) === 0) return false;
  const toggle = el.locator("button").first();
  if ((await toggle.count()) === 0) return false;
  const expanded = await el.getAttribute("data-expanded");
  if (expanded !== "true") {
    await toggle.click();
    await page.waitForTimeout(500);
  }
  return true;
}

async function collapseIfPresent(page, testId) {
  const el = page.getByTestId(testId);
  if ((await el.count()) === 0) return false;
  const expanded = await el.getAttribute("data-expanded");
  if (expanded === "true") {
    await el.locator("button").first().click();
    await page.waitForTimeout(400);
  }
  return true;
}

async function expandLayerCards(page, max = 3) {
  const cards = page.locator("[data-layer-card-expanded]");
  const n = Math.min(await cards.count(), max);
  for (let i = 0; i < n; i++) {
    const card = cards.nth(i);
    if ((await card.getAttribute("data-layer-card-expanded")) !== "true") {
      await card.locator("button").first().click();
      await page.waitForTimeout(300);
    }
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  const { id: workspaceId, url } = await pickWorkspace(page);
  const template =
    (await page.getByTestId("intake-v6-header-template").textContent().catch(() => null)) ??
    "unknown";

  const baseMeta = { url, workspaceId, template };

  // STEP 1
  await gotoStep(page, "layers");
  await shot(page, "01_step1_full", { ...baseMeta, step: 1, state: "initial" });
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "02_step1_top", { ...baseMeta, step: 1, state: "viewport_top" });
  await page.evaluate(() => window.scrollTo(0, 600));
  await shot(page, "03_step1_mid", { ...baseMeta, step: 1, state: "scroll_mid" });
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await shot(page, "04_step1_bottom", { ...baseMeta, step: 1, state: "scroll_bottom" });

  await expandLayerCards(page, 2);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "05_step1_layers_expanded", {
    ...baseMeta,
    step: 1,
    state: "layer_cards_expanded",
  });

  await expandIfPresent(page, "intake-v6-layers-metrics-advanced");
  await shot(page, "06_step1_metrics_expanded", {
    ...baseMeta,
    step: 1,
    state: "metrics_accordion_expanded",
  });

  await collapseIfPresent(page, "intake-v6-layers-metrics-advanced");
  await expandIfPresent(page, "intake-v6-product-composition-panel");
  await shot(page, "07_step1_composition", {
    ...baseMeta,
    step: 1,
    state: "product_composition",
  });

  // STEP 2
  await gotoStep(page, "review");
  await page.waitForTimeout(1200);
  await shot(page, "10_step2_full_initial", { ...baseMeta, step: 2, tab: "finisaje", state: "initial" });

  const tabs = ["finisaje", "iluminare", "montaj"];
  for (const tab of tabs) {
    const tabBtn = page.getByTestId(`intake-v6-review-tab-${tab}`);
    if ((await tabBtn.count()) === 0) continue;
    await tabBtn.click();
    await page.waitForTimeout(700);
    await page.evaluate(() => window.scrollTo(0, 0));
    await shot(page, `11_step2_tab_${tab}_top`, {
      ...baseMeta,
      step: 2,
      tab,
      state: "tab_active_top",
    });
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await shot(page, `12_step2_tab_${tab}_bottom`, {
      ...baseMeta,
      step: 2,
      tab,
      state: "tab_active_bottom",
    });
  }

  await page.getByTestId("intake-v6-review-tab-finisaje").click();
  await expandLayerCards(page, 3);
  await shot(page, "13_step2_finisaje_cards_expanded", {
    ...baseMeta,
    step: 2,
    tab: "finisaje",
    state: "layer_cards_expanded",
  });

  await collapseIfPresent(page, "intake-v6-review-technical-details");
  await shot(page, "14_step2_technical_collapsed", {
    ...baseMeta,
    step: 2,
    state: "technical_details_collapsed",
  });
  await expandIfPresent(page, "intake-v6-review-technical-details");
  await shot(page, "15_step2_technical_expanded", {
    ...baseMeta,
    step: 2,
    state: "technical_details_expanded",
  });

  const backbone = page.getByTestId("form-system-backbone-toggle");
  if ((await backbone.count()) > 0) {
    await backbone.click();
    await page.waitForTimeout(500);
    await shot(page, "16_step2_form_system_expanded", {
      ...baseMeta,
      step: 2,
      state: "form_system_backbone_expanded",
    });
  }

  // STEP 3
  await gotoStep(page, "confirm");
  await page.waitForTimeout(1200);
  await shot(page, "20_step3_full_initial", { ...baseMeta, step: 3, state: "initial" });

  await collapseIfPresent(page, "intake-v6-confirm-operator-summary");
  await shot(page, "21_step3_operator_summary_collapsed", {
    ...baseMeta,
    step: 3,
    state: "operator_summary_collapsed",
  });
  await expandIfPresent(page, "intake-v6-confirm-operator-summary");
  await shot(page, "22_step3_operator_summary_expanded", {
    ...baseMeta,
    step: 3,
    state: "operator_summary_expanded",
  });

  await collapseIfPresent(page, "intake-v6-confirm-technical-details");
  await shot(page, "23_step3_technical_collapsed", {
    ...baseMeta,
    step: 3,
    state: "technical_details_collapsed",
  });
  await expandIfPresent(page, "intake-v6-confirm-technical-details");
  await shot(page, "24_step3_technical_expanded", {
    ...baseMeta,
    step: 3,
    state: "technical_details_expanded",
  });

  await browser.close();
  console.log("DONE workspace:", workspaceId);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
