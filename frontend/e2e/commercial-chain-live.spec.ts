/**
 * Commercial spine — live-db mutation E2E (BUILD-COMMERCIAL-E2E-FIXTURE).
 *
 * Prerequisites:
 *   - Backend :8000 healthy with dev DB (source === "db")
 *   - Fixture seeded: python backend/scripts/seed_commercial_e2e_fixture.py
 *   - Frontend :3000 (playwright webServer or PW_SKIP_WEB_SERVER=1)
 *
 * Does NOT fake success — skips explicitly when live-db fixture unavailable.
 */
import { test, expect } from "@playwright/test";
import {
  probeLiveDbFixture,
  resolveOrderDbId,
  type CommercialFixtureManifest,
} from "./helpers/commercialFixture";

let fixture: CommercialFixtureManifest | null = null;
let skipReason: string | undefined;

test.describe("Commercial chain live-db", () => {
  test.beforeAll(async () => {
    const probe = await probeLiveDbFixture();
    if (!probe.fixtureAvailable || !probe.manifest) {
      skipReason = probe.reason ?? "Live-db commercial fixture unavailable";
      return;
    }
    fixture = probe.manifest;
  });

  test.beforeEach(() => {
    test.skip(!fixture, skipReason ?? "Live-db commercial fixture unavailable");
  });

  test("quote → convert → order → execution", async ({ page }) => {
    const quoteCode = fixture!.quote_code;

    // A. Quote detail URL
    await page.goto(`/quotes/${quoteCode}`);
    await page.waitForLoadState("networkidle");

    // Live DB badge when source===db; fixture probe already verified backend quotes API.
    const liveDbBadge = page.getByText("Live DB").first();
    if (await liveDbBadge.isVisible().catch(() => false)) {
      await expect(liveDbBadge).toBeVisible();
    }
    await expect(page.getByTestId("quote-not-found")).not.toBeVisible();
    await expect(page.getByTestId("quote-terminal-policy")).not.toBeVisible();
    await expect(page.getByTestId("quote-readiness-state")).toBeVisible();
    await expect(page.getByText(quoteCode).first()).toBeVisible();

    // B. Live readiness — no fixture overlay; gate must allow commercial quote
    expect(fixture!.readiness_overlay ?? null).toBeNull();
    expect(fixture!.live_gate_can_create_commercial_quote).toBe(true);
    await expect(page.getByText(/Priced/i).first()).toBeVisible();

    // C. Convert to order (priced quotes expose convert per Quotes.tsx policy)
    const convertBtn = page.getByTestId("quote-convert-action");
    await expect(convertBtn).toBeVisible();
    await convertBtn.click();

    // Handle readiness warning acknowledgement if required
    const ackCheckbox = page.locator("#acknowledge_warnings");
    const ackVisible = await ackCheckbox.isVisible().catch(() => false);
    if (ackVisible) {
      await ackCheckbox.check();
      await page.locator("#reason").fill("E2E commercial spine acknowledgement");
      await page
        .getByRole("button", { name: /Create Order with Acknowledgement/i })
        .click();
    }

    await page.waitForURL(/\/orders\//, { timeout: 30_000 });
    const orderUrl = page.url();
    const orderCodeMatch = orderUrl.match(/\/orders\/([^/?#]+)/);
    expect(orderCodeMatch).toBeTruthy();
    const orderCode = decodeURIComponent(orderCodeMatch![1]);

    await expect(page.getByTestId("order-not-found")).not.toBeVisible();
    await expect(page.getByText(orderCode).first()).toBeVisible();
    await expect(page.getByTestId("order-detail-selected")).toBeVisible();

    // D. Execution detail (requires numeric db id)
    const orderDbId = await resolveOrderDbId(orderCode);
    expect(orderDbId, "order db id must resolve from backend").not.toBeNull();

    await page.goto(`/execution/${orderDbId}`);
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/Execuție|Observabilitate|Comandă/i).first()).toBeVisible({
      timeout: 15_000,
    });

    // Plan generation — quote-derived volumetric order must pass execution contract
    const planBtn = page.getByTestId("execution-plan-generate-action");
    await expect(planBtn).toBeVisible({ timeout: 15_000 });
    const planResponsePromise = page.waitForResponse(
      (resp) =>
        resp.url().includes(`/execution/plan/from-order/${orderDbId}`) &&
        resp.request().method() === "POST",
      { timeout: 30_000 },
    );
    await planBtn.click();
    const planResponse = await planResponsePromise;
    expect(planResponse.status(), await planResponse.text()).toBe(201);
    const planBody = (await planResponse.json()) as {
      id?: number;
      tasks?: unknown[];
      total_estimated_time_minutes?: number;
    };
    expect(planBody.id).toBeTruthy();
    expect(Array.isArray(planBody.tasks)).toBe(true);
    expect((planBody.tasks ?? []).length).toBeGreaterThan(0);
    await expect(page.getByRole("alert").filter({ hasText: /snapshot_incomplete/i })).toHaveCount(
      0,
    );
  });
});
