/**
 * Commercial runtime spine — live-db oriented E2E.
 *
 * Prerequisites:
 * - Backend on :8000 with development DB (source === "db")
 * - Frontend on :3000 (started by playwright webServer or PW_SKIP_WEB_SERVER=1)
 *
 * Full quote→order→execution chain is NOT faked; steps beyond URL selection
 * require writable backend and are skipped when unavailable.
 */
import { test, expect } from "@playwright/test";

test.describe("Commercial spine navigation", () => {
  test("direct quote URL selects quote on refresh", async ({ page }) => {
    await page.goto("/quotes");
    await page.waitForLoadState("networkidle");
    const firstQuote = page.locator('[class*="font-mono"]').filter({ hasText: /^QT-/ }).first();
    const hasQuote = await firstQuote.isVisible().catch(() => false);
    test.skip(!hasQuote, "No quotes in backend — skip direct URL test");

    const quoteId = (await firstQuote.textContent())?.trim() ?? "";
    await page.goto(`/quotes/${quoteId}`);
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(quoteId).first()).toBeVisible();
    await page.reload();
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(quoteId).first()).toBeVisible();
  });

  test("unknown quote id shows non-blocking not found", async ({ page }) => {
    await page.goto("/quotes/QT-NONEXISTENT-E2E");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("quote-not-found")).toBeVisible();
  });

  test("intake preliminary quote opens wizard with volumetric context", async ({
    page,
  }) => {
    await page.goto("/intake/WI-SMOKE-P001");
    await page.waitForLoadState("networkidle");
    const simButton = page.getByTestId("action-open-preliminary-quote");
    const visible = await simButton.isVisible().catch(() => false);
    test.skip(!visible, "WI-SMOKE-P001 not available or no simulate action");

    await simButton.click();
    // Workspace opens embedded volumetric quote tab (or full /quotes wizard from list handoff).
    const embeddedPanel = page.getByTestId("volumetric-quote-panel");
    const listWizard = page.getByTestId("quote-wizard");
    await expect(embeddedPanel.or(listWizard).first()).toBeVisible({
      timeout: 15_000,
    });
  });
});
