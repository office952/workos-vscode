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
const LETTER_ROUTE =
  "http://127.0.0.1:3000/intake-v6/668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c/operator";

async function shot(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("saved", file);
  return file;
}

async function ensureReviewFinisaje(page) {
  const reviewTab = page.getByTestId("intake-v6-wizard-step-review");
  if (await reviewTab.count()) {
    await reviewTab.click();
    await page.waitForTimeout(400);
  }
  await page.getByTestId("intake-v6-review-tab-finisaje").click();
  await page.waitForTimeout(400);
}

async function expandFirstLetterLayer(page) {
  const header = page.locator('[data-testid^="intake-v6-letter-group-header-"]').first();
  if (await header.count()) {
    const expanded = await header.getAttribute("aria-expanded");
    if (expanded !== "true") {
      await header.click();
      await page.waitForTimeout(300);
    }
  }
}

async function readLiveGross(page) {
  const gross = page.getByTestId("intake-v6-live-offer-gross").first();
  if (await gross.count()) return (await gross.textContent())?.trim() ?? null;
  return null;
}

async function collectChecks(page) {
  const finisajePanel = page.getByTestId("intake-v6-review-tab-panel-finisaje");
  const vectorLitereCard = page.getByTestId("intake-v6-letter-group-face-finishes");
  const backingRow = page.getByTestId("intake-v6-backing-finish-row");
  const backingSelect = page.getByTestId("intake-v6-backing-mode");
  const hasVectorLitereCard = (await vectorLitereCard.count()) > 0;

  await expandFirstLetterLayer(page);

  const backingInsideVectorLitere = hasVectorLitereCard
    ? await vectorLitereCard.getByTestId("intake-v6-backing-finish-row").count()
    : 0;
  const integrationInsideVectorLitere = hasVectorLitereCard
    ? await vectorLitereCard.getByTestId("intake-v6-review-backing-finish-integration").count()
    : 0;
  const separateBackingBlock = await page.getByTestId("intake-v6-backing-finish-block").count();

  const backingValue = await backingSelect.inputValue().catch(() => "");
  const backingLabel = await backingSelect.locator("option:checked").textContent().catch(() => "");

  const faceSelect = page.locator('[data-testid^="intake-v6-face-type-"]').first();
  const referenceSelect =
    (await faceSelect.count()) > 0
      ? faceSelect
      : page.locator('[data-testid^="intake-v6-artwork-face-method-"]').first();

  const backingSelectStyles = await backingSelect.evaluate((el) => {
    const cs = getComputedStyle(el);
    return { height: cs.height, fontSize: cs.fontSize, width: cs.width };
  });
  const referenceSelectStyles =
    (await referenceSelect.count()) > 0
      ? await referenceSelect.evaluate((el) => {
          const cs = getComputedStyle(el);
          return { height: cs.height, fontSize: cs.fontSize, width: cs.width };
        })
      : null;

  const backingBox = await backingRow.boundingBox().catch(() => null);
  const referenceBox =
    (await referenceSelect.count()) > 0 ? await referenceSelect.boundingBox().catch(() => null) : null;

  let backingAfterLayers = null;
  if (hasVectorLitereCard && backingBox) {
    const letterLayerCards = page.locator('[data-testid^="intake-v6-letter-group-"]').filter({
      hasNot: page.locator('[data-testid="intake-v6-letter-group-face-finishes"]'),
    });
    const layerCount = await letterLayerCards.count();
    let lastLayerBottom = 0;
    for (let i = 0; i < layerCount; i += 1) {
      const box = await letterLayerCards.nth(i).boundingBox();
      if (box) lastLayerBottom = Math.max(lastLayerBottom, box.y + box.height);
    }
    backingAfterLayers = backingBox.y >= lastLayerBottom - 4;
  }

  return {
    hasVectorLitereCard,
    backingInsideVectorLitereCard: backingInsideVectorLitere > 0,
    integrationInsideVectorLitereCard: integrationInsideVectorLitere > 0,
    backingAfterLayers,
    backingUsesFallbackBlock: separateBackingBlock > 0,
    backingValue,
    backingLabel: backingLabel?.trim(),
    backingSelectStyles,
    referenceSelectStyles,
    backingBox,
    referenceBox,
    finisajePanel,
    vectorLitereCard,
    backingRow,
    backingSelect,
    referenceSelect,
  };
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(ROUTE, { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 });
  await ensureReviewFinisaje(page);

  let state = await collectChecks(page);
  const compositionSummary = await page
    .getByTestId("intake-v6-product-composition-summary")
    .textContent()
    .catch(() => "");

  await state.finisajePanel.scrollIntoViewIfNeeded();
  if ((await state.vectorLitereCard.count()) > 0) {
    await state.vectorLitereCard.scrollIntoViewIfNeeded();
  } else {
    await state.backingRow.scrollIntoViewIfNeeded();
  }
  await shot(page, "01_vector_litere_card_with_backing");

  await expandFirstLetterLayer(page);
  await state.backingRow.scrollIntoViewIfNeeded();
  const clipBase = state.referenceBox ?? state.backingBox;
  const clipBacking = state.backingBox;
  if (clipBacking) {
    await page.screenshot({
      path: path.join(outDir, "02_backing_dropdown_alignment.png"),
      clip: {
        x: Math.max(0, (clipBase?.x ?? clipBacking.x) - 8),
        y: Math.max(0, clipBacking.y - (clipBase ? 120 : 48)),
        width: Math.min(
          1440,
          Math.max(clipBacking.width, clipBase?.width ?? clipBacking.width) + 32,
        ),
        height: Math.min(
          900,
          (clipBase?.height ?? 0) + clipBacking.height + 180,
        ),
      },
    });
    console.log("saved", path.join(outDir, "02_backing_dropdown_alignment.png"));
  } else {
    await shot(page, "02_backing_dropdown_alignment");
  }

  const grossBeforeLedToggle = await readLiveGross(page);

  await page.getByTestId("intake-v6-review-tab-iluminare").click();
  await page.waitForTimeout(400);
  const backingUnderLed = await page
    .getByTestId("intake-v6-review-section-lighting")
    .getByTestId("intake-v6-backing-mode")
    .count();

  await ensureReviewFinisaje(page);
  const illuminatedToggle = page.getByTestId("intake-v6-illuminated");
  if (await illuminatedToggle.count()) {
    const isChecked = await illuminatedToggle.isChecked().catch(() => true);
    if (isChecked) {
      await illuminatedToggle.evaluate((el) => el.click());
      await page.waitForTimeout(500);
    }
  }

  state = await collectChecks(page);
  await state.backingRow.scrollIntoViewIfNeeded();
  await shot(page, "03_led_off_backing_still_visible");

  const grossAfterLedToggle = await readLiveGross(page);

  const validationPage = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await validationPage.goto(LETTER_ROUTE, { waitUntil: "networkidle", timeout: 120000 });
  await validationPage.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 });
  await ensureReviewFinisaje(validationPage);
  const letterFixtureChecks = await collectChecks(validationPage);

  const checks = {
    route: ROUTE,
    compositionSummary: compositionSummary?.trim(),
    hasVectorLitereCardOnRoute: state.hasVectorLitereCard,
    backingInsideVectorLitereCard: state.backingInsideVectorLitereCard,
    integrationInsideVectorLitereCard: state.integrationInsideVectorLitereCard,
    backingAfterLayers: state.backingAfterLayers,
    backingUsesFallbackBlock: state.backingUsesFallbackBlock,
    backingNotUnderLed: backingUnderLed === 0,
    backingVisibleLedOff: (await state.backingSelect.count()) > 0,
    backingValuePreserved:
      state.backingValue === "forex_10_no_bevel" ||
      /fara sanfren/i.test(state.backingLabel ?? ""),
    liveGrossUnchanged:
      grossBeforeLedToggle == null ||
      grossAfterLedToggle == null ||
      grossBeforeLedToggle === grossAfterLedToggle,
    dropdownHeightMatchesReference:
      state.referenceSelectStyles == null ||
      state.backingSelectStyles.height === state.referenceSelectStyles.height,
    dropdownFontMatchesReference:
      state.referenceSelectStyles == null ||
      state.backingSelectStyles.fontSize === state.referenceSelectStyles.fontSize,
    grossBeforeLedToggle,
    grossAfterLedToggle,
    backingValue: state.backingValue,
    backingLabel: state.backingLabel,
    letterFixtureRoute: LETTER_ROUTE,
    letterFixtureBackingInsideVectorLitere: letterFixtureChecks.backingInsideVectorLitereCard,
    letterFixtureIntegrationInsideVectorLitere: letterFixtureChecks.integrationInsideVectorLitereCard,
    letterFixtureBackingAfterLayers: letterFixtureChecks.backingAfterLayers,
  };

  console.log("checks", JSON.stringify(checks, null, 2));

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
