import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(
  __dirname,
  "../../docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_card_fallback_fix",
);
const OWNER_ROUTE =
  "http://127.0.0.1:3000/intake-v6/633b5663-8d15-4dca-805f-4cca202323f6/operator";
const LETTER_ROUTE =
  "http://127.0.0.1:3000/intake-v6/668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c/operator";

async function ensureReviewFinisaje(page) {
  const reviewTab = page.getByTestId("intake-v6-wizard-step-review");
  if (await reviewTab.count()) {
    await reviewTab.click();
    await page.waitForTimeout(400);
  }
  await page.getByTestId("intake-v6-review-tab-finisaje").click();
  await page.waitForTimeout(400);
}

async function readLiveGross(page) {
  const gross = page.getByTestId("intake-v6-live-offer-gross").first();
  return (await gross.count()) ? (await gross.textContent())?.trim() ?? null : null;
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });

  const ownerPage = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await ownerPage.goto(OWNER_ROUTE, { waitUntil: "networkidle", timeout: 120000 });
  await ownerPage.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 });
  await ensureReviewFinisaje(ownerPage);

  const logoCard = ownerPage.getByTestId("intake-v6-artwork-finishes");
  const backingRow = ownerPage.getByTestId("intake-v6-backing-finish-row");
  await logoCard.scrollIntoViewIfNeeded();
  await ownerPage.screenshot({
    path: path.join(outDir, "01_owner_logo_card_with_forex_inside.png"),
    fullPage: false,
  });
  console.log("saved 01");

  const backingBox = await backingRow.boundingBox();
  if (backingBox) {
    await ownerPage.screenshot({
      path: path.join(outDir, "02_owner_logo_forex_alignment.png"),
      clip: {
        x: Math.max(0, backingBox.x - 24),
        y: Math.max(0, backingBox.y - 100),
        width: Math.min(1440, backingBox.width + 48),
        height: Math.min(900, backingBox.height + 140),
      },
    });
    console.log("saved 02");
  }

  const grossBefore = await readLiveGross(ownerPage);
  await ownerPage.getByTestId("intake-v6-review-tab-iluminare").click();
  await ownerPage.waitForTimeout(400);
  const backingUnderLed = await ownerPage
    .getByTestId("intake-v6-review-section-lighting")
    .getByTestId("intake-v6-backing-mode")
    .count();
  const illuminatedToggle = ownerPage.getByTestId("intake-v6-illuminated");
  if (await illuminatedToggle.count()) {
    const isChecked = await illuminatedToggle.isChecked().catch(() => true);
    if (isChecked) await illuminatedToggle.evaluate((el) => el.click());
    await ownerPage.waitForTimeout(500);
  }
  await ensureReviewFinisaje(ownerPage);
  await backingRow.scrollIntoViewIfNeeded();
  await ownerPage.screenshot({
    path: path.join(outDir, "03_owner_logo_led_off_forex_visible.png"),
    fullPage: false,
  });
  console.log("saved 03");

  await ownerPage.reload({ waitUntil: "networkidle" });
  await ensureReviewFinisaje(ownerPage);
  const grossAfterReload = await readLiveGross(ownerPage);
  const ownerChecks = {
    backingInsideLogoCard: (await logoCard.getByTestId("intake-v6-backing-finish-row").count()) > 0,
    noDetachedFallbackBlock: (await ownerPage.getByTestId("intake-v6-backing-finish-block").count()) === 0,
    backingNotUnderLed: backingUnderLed === 0,
    backingVisibleLedOff: (await backingRow.count()) > 0,
    backingValue: await ownerPage.getByTestId("intake-v6-backing-mode").inputValue(),
    grossUnchanged: grossBefore === grossAfterReload,
    grossBefore,
    grossAfterReload,
    note: "LED off may change gross; reload check verifies backing placement does not alter total",
  };

  const letterPage = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await letterPage.goto(LETTER_ROUTE, { waitUntil: "networkidle", timeout: 120000 });
  await ensureReviewFinisaje(letterPage);
  const letterCard = letterPage.getByTestId("intake-v6-letter-group-face-finishes");
  await letterCard.scrollIntoViewIfNeeded();
  const letterCardBox = await letterCard.boundingBox();
  if (letterCardBox) {
    await letterPage.screenshot({
      path: path.join(outDir, "04_letter_card_with_forex_inside.png"),
      clip: {
        x: Math.max(0, letterCardBox.x - 8),
        y: Math.max(0, letterCardBox.y - 4),
        width: Math.min(1440, letterCardBox.width + 16),
        height: Math.min(900, letterCardBox.height + 8),
      },
    });
  }
  console.log("saved 04");

  const letterChecks = {
    backingInsideLetterCard: (await letterCard.getByTestId("intake-v6-backing-finish-row").count()) > 0,
    noBackingInLogoCard: (await letterPage.getByTestId("intake-v6-artwork-finishes").count()) === 0
      ? true
      : (await letterPage.getByTestId("intake-v6-artwork-finishes").getByTestId("intake-v6-backing-finish-row").count()) === 0,
    noDetachedFallbackBlock: (await letterPage.getByTestId("intake-v6-backing-finish-block").count()) === 0,
  };

  console.log("ownerChecks", JSON.stringify(ownerChecks, null, 2));
  console.log("letterChecks", JSON.stringify(letterChecks, null, 2));

  const failed = [
    !ownerChecks.backingInsideLogoCard && "owner:backingInsideLogoCard",
    !ownerChecks.noDetachedFallbackBlock && "owner:noDetachedFallbackBlock",
    !ownerChecks.backingNotUnderLed && "owner:backingNotUnderLed",
    !ownerChecks.backingVisibleLedOff && "owner:backingVisibleLedOff",
    ownerChecks.backingValue !== "forex_10_no_bevel" && "owner:backingValue",
    !ownerChecks.grossUnchanged && "owner:grossUnchanged",
    !letterChecks.backingInsideLetterCard && "letter:backingInsideLetterCard",
    !letterChecks.noBackingInLogoCard && "letter:noBackingInLogoCard",
    !letterChecks.noDetachedFallbackBlock && "letter:noDetachedFallbackBlock",
  ].filter(Boolean);

  await browser.close();
  if (failed.length > 0) {
    console.error("FAILED", failed.join(", "));
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
