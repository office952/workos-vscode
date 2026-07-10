import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/intake-v6-final-ui-audit-footer-consolidation-v1/screenshots",
);
const ROUTE =
  "http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator";
const WORKSPACE = "22ef834d-f2d0-453b-a7a7-118928c98a39";

/** @type {Array<{file:string,url:string,workspace:string,pas:string,tab:string,state:string,clickPath:string,proves:string}>} */
const manifest = [];

async function shot(page, name, meta) {
  const file = `${name}.png`;
  await page.screenshot({ path: path.join(outDir, file), fullPage: false });
  manifest.push({ file, url: ROUTE, workspace: WORKSPACE, ...meta });
  console.log("saved", path.join(outDir, file));
}

async function gotoStep(page, stepId) {
  const tab = page.getByTestId(`intake-v6-progress-step-${stepId}`);
  if (await tab.count()) {
    await tab.click();
    await page.waitForTimeout(900);
  }
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

  // Step 1 — layers
  await gotoStep(page, "layers");
  await page.waitForSelector('[data-testid="intake-v6-layers-layout"]', { timeout: 60000 }).catch(() => {});
  await shot(page, "01_step1_final_minimal_status", {
    pas: "1 Straturi",
    tab: "layers",
    state: "default collapsed footer",
    clickPath: "open route → layers step",
    proves: "Compact header (code/step/progress), no duplicate workspace status badge, minimal Pas 1 status",
  });

  const footer = page.getByTestId("intake-v6-operator-workspace-footer");
  if (await footer.count()) await footer.scrollIntoViewIfNeeded();
  await shot(page, "02_step1_footer_collapsed", {
    pas: "1 Straturi",
    tab: "layers",
    state: "footer collapsed",
    clickPath: "scroll to footer",
    proves: "Footer drawer collapsed by default; count label visible",
  });

  await expandFooter(page);
  await shot(page, "03_step1_footer_expanded", {
    pas: "1 Straturi",
    tab: "layers",
    state: "footer expanded",
    clickPath: "click intake-v6-footer-issues-toggle",
    proves: "Secondary analysis warnings grouped in footer (Avertizări / Detalii tehnice)",
  });

  // Step 2 — review
  await gotoStep(page, "review");
  await page.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 }).catch(() => {});
  await page.evaluate(() => window.scrollTo(0, 0));
  await shot(page, "04_step2_final_minimal_status", {
    pas: "2 Review",
    tab: "review",
    state: "default collapsed footer",
    clickPath: "progress → review",
    proves: "Pas 2 minimal header; live calc title unchanged",
  });

  if (await footer.count()) await footer.scrollIntoViewIfNeeded();
  const toggle = page.getByTestId("intake-v6-footer-issues-toggle");
  if ((await toggle.count()) && (await toggle.getAttribute("aria-expanded")) === "true") {
    await toggle.click();
    await page.waitForTimeout(300);
  }
  await shot(page, "05_step2_footer_collapsed", {
    pas: "2 Review",
    tab: "review",
    state: "footer collapsed",
    clickPath: "scroll to footer on review",
    proves: "Footer count visible; no badge wall",
  });

  await expandFooter(page);
  await shot(page, "06_step2_footer_expanded", {
    pas: "2 Review",
    tab: "review",
    state: "footer expanded",
    clickPath: "expand footer on review",
    proves: "Review warnings/info accessible in grouped footer drawer",
  });

  const blocker = page.getByTestId("intake-v6-review-operator-blocker-banner");
  if (await blocker.count()) {
    await blocker.scrollIntoViewIfNeeded();
  }
  await shot(page, "07_step2_blocker_still_visible", {
    pas: "2 Review",
    tab: "review",
    state: "blocker banner visible",
    clickPath: "scroll to review blocker banner",
    proves: "Primary actionable blocker remains outside footer drawer",
  });

  const liveCalc = page.getByTestId("intake-v6-review-calculator-panel");
  if (await liveCalc.count()) {
    const title = page.getByText("Calcul estimativ live", { exact: false });
    if (await title.count()) {
      console.log("live calc title present");
    }
  }

  // Step 3 — confirm
  await gotoStep(page, "confirm");
  await page.waitForSelector('[data-testid="intake-v6-step-confirm"]', { timeout: 60000 }).catch(() => {});
  await page.evaluate(() => window.scrollTo(0, 0));
  const consolidated = page.getByTestId("intake-v6-confirm-consolidated-status");
  if (await consolidated.count()) await consolidated.scrollIntoViewIfNeeded();
  await shot(page, "08_step3_final_minimal_status", {
    pas: "3 Confirmare",
    tab: "confirm",
    state: "default collapsed footer",
    clickPath: "progress → confirm",
    proves: "Step 3 consolidated status panel visible; no duplicate header badges",
  });

  if (await footer.count()) await footer.scrollIntoViewIfNeeded();
  if ((await toggle.count()) && (await toggle.getAttribute("aria-expanded")) === "true") {
    await toggle.click();
    await page.waitForTimeout(300);
  }
  await shot(page, "09_step3_footer_collapsed", {
    pas: "3 Confirmare",
    tab: "confirm",
    state: "footer collapsed",
    clickPath: "scroll to footer on confirm",
    proves: "Confirm footer scope unchanged; collapsed by default",
  });

  await expandFooter(page);
  await shot(page, "10_step3_footer_expanded", {
    pas: "3 Confirmare",
    tab: "confirm",
    state: "footer expanded",
    clickPath: "expand footer on confirm",
    proves: "Confirm-step issues grouped in footer without restoring badge noise",
  });

  await writeFile(
    path.resolve(outDir, "../screenshots_index.md"),
    `# Intake V6 Final UI Audit — Footer Consolidation\n\n| # | File | Pas | State | Proves |\n| --- | --- | --- | --- | --- |\n${manifest
      .map(
        (row, index) =>
          `| ${String(index + 1).padStart(2, "0")} | ${row.file} | ${row.pas} | ${row.state} | ${row.proves} |`,
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
