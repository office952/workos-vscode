/**
 * Configurator letter pilot — after screenshots.
 * Runtime: FE :3001 · workspace with letter_group_finishes.
 */
import fs from "fs";
import path from "path";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");
const OUT = path.join(__dirname, "screenshots");
fs.mkdirSync(OUT, { recursive: true });

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3001";
const WS =
  process.env.PW_WORKSPACE_ID ?? "e1ba14f2-ceca-4239-9e8e-e87c0e21d65f";
const URL = `${UI}/intake-v6/${WS}/operator`;

async function shot(page, name) {
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", name, file);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.waitForSelector('[data-testid="intake-v6-progress-step-review"], [data-testid="intake-v6-review-tab-finisaje"]', {
    timeout: 90_000,
  });
  await page.waitForTimeout(2000);

  // Step 2 Configurare
  const review = page.getByTestId("intake-v6-progress-step-review");
  if ((await review.count()) > 0) {
    await review.click({ force: true });
    await page.waitForTimeout(1500);
  }

  await page.getByTestId("intake-v6-review-tab-finisaje").click({ force: true });
  await page.waitForTimeout(1000);

  const letterCluster = page.getByTestId("intake-v6-letter-group-face-finishes");
  if ((await letterCluster.count()) > 0) {
    await letterCluster.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
  }
  await shot(page, "03_letter_anatomy_presentation");

  const letterHeader = page.getByTestId(/intake-v6-letter-group-header-/).first();
  if ((await letterHeader.count()) > 0) {
    await letterHeader.scrollIntoViewIfNeeded();
    const expanded = await page
      .locator('[data-testid^="intake-v6-letter-group-"][data-layer-card-expanded="true"]')
      .count();
    if (expanded === 0) {
      await letterHeader.click();
      await page.waitForTimeout(600);
    }
    const faceZone = page.locator('[data-testid^="intake-v6-face-letter-zone-"]').first();
    if ((await faceZone.count()) > 0) {
      await faceZone.scrollIntoViewIfNeeded();
    } else {
      await letterHeader.scrollIntoViewIfNeeded();
    }
    await page.waitForTimeout(400);
    await shot(page, "04_face_cant_back_grouping");
  } else {
    console.warn("No letter group header — skipping 04");
  }

  await page.getByTestId("intake-v6-review-tab-iluminare").click();
  await page.waitForTimeout(1000);
  const lighting = page.getByTestId("intake-v6-review-lighting-section");
  if ((await lighting.count()) > 0) {
    await lighting.scrollIntoViewIfNeeded();
  }
  await page.waitForTimeout(400);
  await shot(page, "05_lighting_grouping");

  const results = page.getByTestId("intake-v6-lighting-results");
  if ((await results.count()) > 0) {
    await results.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    await shot(page, "06_result_summary");
  } else {
    // Fall back: scroll within lighting section footer / accordion area
    const lightingFooter = page.getByTestId("intake-v6-led-calculation-details");
    if ((await lightingFooter.count()) > 0) {
      await lightingFooter.scrollIntoViewIfNeeded();
      await page.waitForTimeout(400);
    }
    console.warn("No lighting results panel — capturing lighting section bottom as 06");
    await shot(page, "06_result_summary");
  }

  await page.getByTestId("intake-v6-review-tab-finisaje").click();
  await page.waitForTimeout(800);
  const ownership = page.getByTestId("intake-v6-finish-ownership-note");
  if ((await ownership.count()) > 0) {
    await ownership.scrollIntoViewIfNeeded();
    const expandedAttr = await ownership.getAttribute("data-expanded");
    if (expandedAttr === "true") {
      await page.getByTestId("intake-v6-finish-ownership-note-toggle").click();
      await page.waitForTimeout(300);
    }
    await shot(page, "07_technical_disclosure_collapsed");
    await page.getByTestId("intake-v6-finish-ownership-note-toggle").click();
    await page.waitForTimeout(400);
    await shot(page, "08_technical_disclosure_expanded");
  } else {
    console.warn("No finish ownership accordion — skipping 07/08");
  }

  const confirm = page.getByTestId("intake-v6-progress-step-confirm");
  if ((await confirm.count()) > 0) {
    await confirm.click();
    await page.waitForTimeout(2000);
    await page.evaluate(() => window.scrollTo(0, 0));
    await shot(page, "09_confirmation_summary");
  }

  // Return to Configurare for probes (Confirmare hides review tabs)
  const reviewAgain = page.getByTestId("intake-v6-progress-step-review");
  if ((await reviewAgain.count()) > 0) {
    await reviewAgain.click({ force: true });
    await page.waitForTimeout(1200);
  }
  await page.getByTestId("intake-v6-review-tab-finisaje").click({ force: true });
  await page.waitForTimeout(600);
  const finisajeProbe = await page.evaluate(() => ({
    letterTitle: !!document.querySelector(
      '[data-testid="intake-v6-letter-group-face-finishes"]',
    ),
    anatomy: !!document.querySelector('[data-testid="intake-v6-letter-anatomy-legend"]'),
    artworkCluster: !!document.querySelector('[data-testid="intake-v6-artwork-finishes"]'),
  }));
  await page.getByTestId("intake-v6-review-tab-iluminare").click({ force: true });
  await page.waitForTimeout(600);
  const iluminareProbe = await page.evaluate(() => ({
    results: !!document.querySelector('[data-testid="intake-v6-lighting-results"]'),
    decisions: document.body.innerText.includes("Decizii iluminare"),
  }));

  // Smoke: Montaj tab still present (no redesign)
  await page.getByTestId("intake-v6-review-tab-montaj").click({ force: true });
  await page.waitForTimeout(800);
  const montajOk = (await page.getByTestId("intake-v6-review-tab-panel-montaj").count()) > 0;
  console.log("montaj_panel_present", montajOk);
  console.log("probe", JSON.stringify({ ...finisajeProbe, ...iluminareProbe }));
  fs.writeFileSync(
    path.join(__dirname, "capture_meta.json"),
    JSON.stringify(
      {
        url: URL,
        workspace: WS,
        ui: UI,
        probe: { ...finisajeProbe, ...iluminareProbe },
        montajOk,
        at: new Date().toISOString(),
      },
      null,
      2,
    ),
  );

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
