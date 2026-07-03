/**
 * Smoke test for internal commercial spine demo route (read-only, no mutations).
 */
import { test, expect } from "@playwright/test";
import {
  FIXTURE_QUOTE_CODE,
  FIXTURE_WARN_QUOTE_CODE,
} from "./helpers/commercialFixture";

test.describe("Commercial spine demo page", () => {
  test("loads internal demo with both scenario cards and quote links", async ({ page }) => {
    await page.goto("/demo/commercial-spine");
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("commercial-spine-demo-page")).toBeVisible();
    await expect(page.getByTestId("commercial-spine-demo-internal-label")).toHaveText(
      /Internal Demo/i
    );
    await expect(page.getByText("Internal Commercial Spine Demo")).toBeVisible();

    await expect(page.getByTestId("demo-scenario-ready")).toBeVisible();
    await expect(page.getByTestId("demo-scenario-warn")).toBeVisible();

    await expect(page.getByTestId("demo-proof-summary")).toBeVisible();
    await expect(page.getByTestId("demo-command-panel")).toBeVisible();
    await expect(page.getByTestId("demo-caveat-panel")).toBeVisible();
    await expect(page.getByTestId("demo-proof-summary")).toContainText("readiness_overlay");

    await expect(page.getByTestId("demo-link-quote-ready")).toHaveAttribute(
      "href",
      `/quotes/${FIXTURE_QUOTE_CODE}`
    );
    await expect(page.getByTestId("demo-link-quote-warn")).toHaveAttribute(
      "href",
      `/quotes/${FIXTURE_WARN_QUOTE_CODE}`
    );
  });
});
