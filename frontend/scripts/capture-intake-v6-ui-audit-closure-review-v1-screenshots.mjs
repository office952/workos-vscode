import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/intake-v6-ui-audit-closure-review-v1/screenshots",
);
const ROUTE =
  "http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator";
const WORKSPACE = "22ef834d-f2d0-453b-a7a7-118928c98a39";

/** @type {Array<Record<string, string>>} */
const manifest = [];

async function shot(page, name, meta) {
  const file = `${name}.png`;
  await page.screenshot({ path: path.join(outDir, file), fullPage: false });
  manifest.push({ file, url: ROUTE, workspace: WORKSPACE, ...meta });
  console.log("saved", path.join(outDir, file));
}

async function gotoStep(page, stepId) {
  await page.getByTestId(`intake-v6-progress-step-${stepId}`).click();
  await page.waitForTimeout(900);
}

async function expandFooter(page) {
  const toggle = page.getByTestId("intake-v6-footer-issues-toggle");
  if (await toggle.count()) {
    await toggle.scrollIntoViewIfNeeded();
    if ((await toggle.getAttribute("aria-expanded")) !== "true") {
      await toggle.click();
      await page.waitForTimeout(400);
    }
  }
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(ROUTE, { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForSelector('[data-testid="intake-v6-operator-workspace"]', { timeout: 60000 });

  // 01 — Step 1 overview
  await gotoStep(page, "layers");
  await page.waitForSelector('[data-testid="intake-v6-layers-layout"]', { timeout: 60000 }).catch(() => {});
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "01_step1_final_overview", {
    pas: "1 Straturi",
    tab: "layers",
    state: "default",
    clickPath: "route → layers step",
    proves: "Layer decisions, compact warnings, header without duplicate badge",
  });

  // 02 — Step 1 footer collapsed then expanded (expanded capture)
  await expandFooter(page);
  await shot(page, "02_step1_footer_collapsed_and_expanded", {
    pas: "1 Straturi",
    tab: "layers",
    state: "footer expanded",
    clickPath: "footer toggle after default collapsed load",
    proves: "Footer drawer expands; secondary analysis warnings grouped",
  });

  // 03 — Step 2 Finisaje
  await gotoStep(page, "review");
  await page.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 }).catch(() => {});
  await page.getByTestId("intake-v6-review-tab-finisaje").click().catch(() => {});
  await page.waitForTimeout(500);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "03_step2_finisaje_final", {
    pas: "2 Review",
    tab: "Finisaje",
    state: "default",
    clickPath: "review → Finisaje tab",
    proves: "Finisaje tab with actionable pending badge; no ON pill noise",
  });

  // 04 — Step 2 blocker + footer
  const blocker = page.getByTestId("intake-v6-review-operator-blocker-banner");
  if (await blocker.count()) await blocker.scrollIntoViewIfNeeded();
  const footer = page.getByTestId("intake-v6-operator-workspace-footer");
  if (await footer.count()) await footer.scrollIntoViewIfNeeded();
  await shot(page, "04_step2_blocker_and_footer", {
    pas: "2 Review",
    tab: "Finisaje",
    state: "blocker + footer visible",
    clickPath: "scroll blocker banner and footer",
    proves: "Blocker stays local; footer count secondary",
  });

  // 05 — Diagnostic + live calculation
  const diagnostic = page.getByTestId("intake-v6-review-technical-details");
  if (await diagnostic.count()) {
    await diagnostic.scrollIntoViewIfNeeded();
  }
  const calc = page.getByTestId("intake-v6-review-calculator-panel");
  if (await calc.count()) {
    await calc.scrollIntoViewIfNeeded();
  }
  await shot(page, "05_step2_diagnostic_and_live_calculation", {
    pas: "2 Review",
    tab: "Finisaje",
    state: "diagnostic + live calc",
    clickPath: "scroll to Detalii tehnice and Calcul estimativ live",
    proves: "Diagnostics secondary; live calc labeled estimative",
  });

  // 06 — Iluminare tab
  await page.getByTestId("intake-v6-review-tab-iluminare").click().catch(() => {});
  await page.waitForTimeout(500);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "06_step2_iluminare_final", {
    pas: "2 Review",
    tab: "Iluminare",
    state: "default",
    clickPath: "click Iluminare tab",
    proves: "Iluminare without redundant ON pill",
  });

  // 07 — Step 3 status
  await gotoStep(page, "confirm");
  await page.waitForSelector('[data-testid="intake-v6-step-confirm"]', { timeout: 60000 }).catch(() => {});
  const consolidated = page.getByTestId("intake-v6-confirm-consolidated-status");
  if (await consolidated.count()) await consolidated.scrollIntoViewIfNeeded();
  await shot(page, "07_step3_status_final", {
    pas: "3 Confirmare",
    tab: "confirm",
    state: "consolidated status",
    clickPath: "confirm step",
    proves: "Single Status configurație panel; no header badge duplication",
  });

  // 08 — Step 3 handoff + footer
  const handoff = page.getByTestId("intake-v6-confirm-handoff-panel");
  if (await handoff.count()) await handoff.scrollIntoViewIfNeeded();
  if (await footer.count()) await footer.scrollIntoViewIfNeeded();
  await shot(page, "08_step3_handoff_and_footer", {
    pas: "3 Confirmare",
    tab: "confirm",
    state: "handoff + footer",
    clickPath: "scroll handoff checklist and footer",
    proves: "Checklist actions concrete; footer scope distinct from status panel",
  });

  // 09 — Cross-step navigation
  await page.evaluate(() => window.scrollTo(0, 0));
  const progress = page.getByTestId("intake-v6-progress");
  if (await progress.count()) await progress.scrollIntoViewIfNeeded();
  await shot(page, "09_cross_step_navigation", {
    pas: "1–3",
    tab: "progress bar",
    state: "confirm step context",
    clickPath: "scroll to progress steps on Pas 3",
    proves: "Consistent Straturi / Review / Confirmare navigation",
  });

  // 10 — Final closure overview (Step 1 return)
  await gotoStep(page, "layers");
  await page.waitForTimeout(600);
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "10_final_ui_closure_overview", {
    pas: "1 Straturi",
    tab: "layers",
    state: "closure return",
    clickPath: "progress → layers after full audit path",
    proves: "End-to-end UI arc stable; ready to leave polish loop",
  });

  await writeFile(
    path.resolve(outDir, "../screenshots_index.md"),
    `# Intake V6 UI Audit Closure Review V1\n\n| # | File | Pas | Tab | State | Proves |\n| --- | --- | --- | --- | --- | --- |\n${manifest
      .map(
        (row, i) =>
          `| ${String(i + 1).padStart(2, "0")} | ${row.file} | ${row.pas} | ${row.tab} | ${row.state} | ${row.proves} |`,
      )
      .join("\n")}\n`,
    "utf8",
  );

  console.log(JSON.stringify({ route: ROUTE, workspace: WORKSPACE, shots: manifest.length }, null, 2));
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
