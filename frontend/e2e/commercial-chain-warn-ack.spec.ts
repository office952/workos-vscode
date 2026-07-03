/**
 * Commercial spine — WARN acknowledgement path (BUILD-COMMERCIAL-WARN-ACK-E2E).
 *
 * Prerequisites:
 *   - Backend :8000 healthy with dev DB
 *   - Fixture seeded: python backend/scripts/seed_commercial_e2e_fixture.py
 *   - WARN quote QT-E2E-COMMERCIAL-WARN-001 priced, requires_acknowledgement
 *   - Frontend :3000 (playwright webServer or PW_SKIP_WEB_SERVER=1)
 *
 * Proves browser gating: convert disabled until inline acknowledgement, then succeeds.
 */
import { test, expect } from "@playwright/test";
import {
  probeWarnLiveDbFixture,
  resolveOrderDbId,
  type WarnFixtureManifest,
} from "./helpers/commercialFixture";

let warnFixture: WarnFixtureManifest | null = null;
let readinessOverlay: string | null = null;
let skipReason: string | undefined;

test.describe("Commercial chain warn acknowledgement live-db", () => {
  test.beforeAll(async () => {
    const probe = await probeWarnLiveDbFixture();
    readinessOverlay = probe.readiness_overlay;
    if (!probe.fixtureAvailable || !probe.manifest) {
      skipReason = probe.reason ?? "WARN live-db fixture unavailable";
      return;
    }
    warnFixture = probe.manifest;
  });

  test.beforeEach(() => {
    test.skip(!warnFixture, skipReason ?? "WARN live-db fixture unavailable");
  });

  test("warn quote requires acknowledgement before convert → order → execution", async ({
    page,
  }) => {
    const quoteCode = warnFixture!.quote_code;
    const ackPendingCode = warnFixture!.quote_gate_ack_pending[0];

    // Manifest contract — no overlay, gate allows quote with ack pending
    expect(readinessOverlay ?? null).toBeNull();
    expect(warnFixture!.can_create_commercial_quote).toBe(true);
    expect(warnFixture!.requires_acknowledgement).toBe(true);
    expect(warnFixture!.quote_gate_ack_pending.length).toBeGreaterThan(0);

    await page.goto(`/quotes/${quoteCode}`);
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("quote-not-found")).not.toBeVisible();
    await expect(page.getByText(quoteCode).first()).toBeVisible();

    // Volumetric readiness panel + acknowledgement state
    const readinessPanel = page.getByTestId("quote-volumetric-readiness");
    await expect(readinessPanel).toBeVisible();
    await expect(page.getByTestId("quote-volumetric-readiness-status")).toHaveText(
      /Requires acknowledgement/i
    );
    const ackPendingSection = page.getByTestId("quote-volumetric-readiness-ack-pending");
    await expect(ackPendingSection).toBeVisible();
    await expect(ackPendingSection.getByText(`(${ackPendingCode})`)).toBeVisible();
    if (ackPendingCode === "operations_missing") {
      await expect(ackPendingSection.getByText(/operațiile/i)).toBeVisible();
    }

    const convertBtn = page.getByTestId("quote-convert-action");
    await expect(convertBtn).toBeVisible();
    await expect(convertBtn).toBeDisabled();
    await expect(page.getByTestId("quote-convert-ack-hint")).toBeVisible();

    const ackCheckbox = page.locator("#quote_convert_acknowledge_warnings");
    await expect(ackCheckbox).toBeVisible();
    await expect(ackCheckbox).not.toBeChecked();

    await ackCheckbox.check();
    await expect(ackCheckbox).toBeChecked();
    await expect(convertBtn).toBeEnabled();

    await convertBtn.click();

    await page.waitForURL(/\/orders\//, { timeout: 30_000 });
    const orderUrl = page.url();
    const orderCodeMatch = orderUrl.match(/\/orders\/([^/?#]+)/);
    expect(orderCodeMatch).toBeTruthy();
    const orderCode = decodeURIComponent(orderCodeMatch![1]);

    await expect(page.getByTestId("order-not-found")).not.toBeVisible();
    await expect(page.getByText(orderCode).first()).toBeVisible();
    await expect(page.getByTestId("order-detail-selected")).toBeVisible();

    const orderDbId = await resolveOrderDbId(orderCode);
    expect(orderDbId, "order db id must resolve from backend").not.toBeNull();

    await page.goto(`/execution/${orderDbId}`);
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/Execuție|Observabilitate|Comandă/i).first()).toBeVisible({
      timeout: 15_000,
    });

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
    };
    expect(planBody.id).toBeTruthy();
    expect(Array.isArray(planBody.tasks)).toBe(true);
    expect((planBody.tasks ?? []).length).toBeGreaterThan(0);
    await expect(page.getByRole("alert").filter({ hasText: /snapshot_incomplete/i })).toHaveCount(
      0,
    );
  });
});
