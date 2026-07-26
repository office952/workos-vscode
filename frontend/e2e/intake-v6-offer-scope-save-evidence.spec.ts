import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const WORKSPACE_ROUTE_CODE = "IR-MRI01769";
const UI_BASE = process.env.INTAKE_V6_UI_BASE ?? "http://127.0.0.1:3000";
const OPERATOR_URL = `${UI_BASE}/intake-v6/${WORKSPACE_ROUTE_CODE}/operator`;

const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-frontend-offer-scope-save-state-debug-v1/screenshots",
);
const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-frontend-offer-scope-save-state-debug-v1/evidence_report.json",
);

test("capture offer-scope save state evidence", async ({ page }) => {
  test.setTimeout(300_000);
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const putLog: Array<{ status: number; durationMs: number; body: string }> = [];
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("response", async (response) => {
    if (response.url().includes("/offer-scope") && response.request().method() === "PUT") {
      const timing = response.request().timing();
      putLog.push({
        status: response.status(),
        durationMs: timing.responseEnd > 0 ? timing.responseEnd : 0,
        body: (await response.text()).slice(0, 500),
      });
    }
  });

  await page.goto(OPERATOR_URL, { waitUntil: "networkidle", timeout: 120_000 });
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });

  const status = page.getByTestId("intake-v6-offer-scope-status");
  await page.screenshot({ path: path.join(OUT_DIR, "01_before_save.png"), fullPage: true });

  if (!(await page.getByTestId("intake-v6-offer-scope-mode-full").isChecked())) {
    await page.getByTestId("intake-v6-offer-scope-mode-full").click({ force: true });
    await expect(status).toHaveText("Selecție confirmată", { timeout: 60_000 });
  }

  await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
  const putPromise = page.waitForResponse(
    (r) => r.url().includes("/offer-scope") && r.request().method() === "PUT" && r.ok(),
    { timeout: 120_000 },
  );
  await page.getByTestId("intake-v6-offer-scope-back").check({ force: true });
  await putPromise;

  await expect(status).not.toContainText("Salvez selecția", { timeout: 30_000 });
  await expect(status).toHaveText("Selecție confirmată", { timeout: 30_000 });
  await page.screenshot({ path: path.join(OUT_DIR, "02_after_200_saving_cleared.png"), fullPage: true });

  for (let i = 0; i < 9; i += 1) {
    const toggle = i % 2 === 0 ? "intake-v6-offer-scope-lighting" : "intake-v6-offer-scope-back";
    const checkbox = page.getByTestId(toggle);
    if (await checkbox.isChecked()) {
      await checkbox.uncheck({ force: true });
    } else {
      await checkbox.check({ force: true });
    }
    await expect(status).not.toContainText("Salvez selecția", { timeout: 60_000 });
  }

  await page.reload({ waitUntil: "networkidle", timeout: 120_000 });
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });
  await page.screenshot({ path: path.join(OUT_DIR, "03_reload_persisted.png"), fullPage: true });

  if (await page.getByTestId("intake-v6-offer-scope-mode-full").isChecked()) {
    await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
  }
  for (const testId of [
    "intake-v6-offer-scope-face",
    "intake-v6-offer-scope-cant",
    "intake-v6-offer-scope-back",
    "intake-v6-offer-scope-lighting",
    "intake-v6-offer-scope-electrical",
  ]) {
    const checkbox = page.getByTestId(testId);
    if (await checkbox.isChecked()) {
      await checkbox.uncheck({ force: true });
    }
  }
  await expect(page.getByTestId("intake-v6-offer-scope-empty-subset-error")).toBeVisible({ timeout: 15_000 });
  await page.getByTestId("intake-v6-offer-scope-back").check({ force: true });
  await expect(status).toHaveText("Selecție confirmată", { timeout: 60_000 });
  await page.getByTestId("intake-v6-offer-scope-lighting").check({ force: true });
  await expect(status).toHaveText("Selecție confirmată", { timeout: 60_000 });
  await expect(status).not.toContainText("Salvez selecția", { timeout: 30_000 });
  await page.screenshot({ path: path.join(OUT_DIR, "04_empty_to_back_lighting_stable.png"), fullPage: true });

  await page.waitForTimeout(60_000);
  await expect(status).not.toContainText("Salvez selecția", { timeout: 5_000 });

  fs.writeFileSync(
    REPORT_PATH,
    JSON.stringify(
      {
        task: "INTAKE_V6_FRONTEND_OFFER_SCOPE_SAVE_STATE_DEBUG_V1",
        workspace_code: WORKSPACE_ROUTE_CODE,
        route: OPERATOR_URL,
        captured_at: new Date().toISOString(),
        classification: "FRONTEND_MULTIPLE_SAVING_SOURCES",
        root_cause:
          "Persist queue retried failed intents and workspace phase could remain persisting while panel saving stuck; PERSIST_SUCCESS also advanced step away from layers.",
        saving_state_source: "IntakeV6OfferScopePanel.saving (authoritative UI); workspace phase persisting only disables controls",
        put_log: putLog,
        network_summary: {
          offer_scope_put_count: putLog.length,
          all_http_200: putLog.every((entry) => entry.status >= 200 && entry.status < 300),
        },
        console_summary: {
          error_count: consoleErrors.length,
          errors: consoleErrors.slice(0, 20),
        },
        soak_seconds: 60,
        screenshots: [
          "01_before_save.png",
          "02_after_200_saving_cleared.png",
          "03_reload_persisted.png",
          "04_empty_to_back_lighting_stable.png",
        ],
      },
      null,
      2,
    ),
  );
});
