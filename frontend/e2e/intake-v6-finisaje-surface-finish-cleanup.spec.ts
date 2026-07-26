/**
 * Live Finisaje SURFACE_FINISH ownership demotion:
 * raw tokens absent from primary chrome; technical disclosure collapsed by default;
 * Montaj IA frozen.
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BACKEND = process.env.PW_BACKEND_URL ?? "http://127.0.0.1:8003";
const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3001";
const SVG = path.join(
  process.env.USERPROFILE || process.env.HOME || "",
  "Desktop",
  "fisiere-teste-svg",
  "litere-cu-fundal-acm-segmentat.svg",
);
const OUT = path.join(
  __dirname,
  "..",
  "..",
  "docs",
  "qa",
  "intake-v6-finisaje-surface-finish-cleanup-2026-07-19",
  "screenshots",
);

async function createWorkspace(title: string) {
  const response = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, analyzer_mode: "analyzer_first" }),
  });
  if (!response.ok) throw new Error(`workspace create ${response.status}`);
  return response.json() as Promise<{ id: string; workspace_code: string }>;
}

async function getWorkspace(id: string) {
  const response = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${id}`);
  if (!response.ok) throw new Error(`workspace get ${response.status}`);
  return response.json();
}

async function waitAuth(page: Page) {
  await expect(page.getByText("Se verifică sesiunea")).toHaveCount(0, { timeout: 60_000 });
}

async function shot(page: Page, name: string) {
  fs.mkdirSync(OUT, { recursive: true });
  await page.screenshot({ path: path.join(OUT, name), fullPage: true });
}

async function confirmRolesAndContinue(page: Page) {
  const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
    await page.waitForTimeout(1200);
  }
  await expect(page.getByTestId("intake-v6-footer-next")).toBeEnabled({ timeout: 90_000 });
  await page.getByTestId("intake-v6-footer-next").click();
  await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 90_000 });
}

test.describe("Intake V6 Finisaje SURFACE_FINISH cleanup", () => {
  test.use({ viewport: { width: 1440, height: 960 } });

  test("primary Finisaje hides raw ownership tokens; Montaj frozen", async ({ page }) => {
    test.setTimeout(300_000);
    expect(fs.existsSync(SVG)).toBe(true);
    const ws = await createWorkspace(`finisaje-ownership-${Date.now()}`);

    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await waitAuth(page);
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 90_000 });

    await page.getByTestId("intake-v6-svg-input").setInputFiles(SVG);
    await expect(page.getByTestId("intake-v6-file-confirm-chip")).toBeVisible({ timeout: 90_000 });

    const started = Date.now();
    while (Date.now() - started < 60_000) {
      const snap = await getWorkspace(ws.id);
      if (snap?.payload?.svg_analysis_json) break;
      await page.waitForTimeout(800);
    }

    await confirmRolesAndContinue(page);
    await page.getByTestId("intake-v6-review-tab-finisaje").click();
    await expect(page.getByTestId("intake-v6-review-tab-panel-finisaje")).toBeVisible();

    await shot(page, "01_finisaje_initial.png");
    await shot(page, "02_active_finish_controls.png");
    await shot(page, "10_full_finisaje_tab.png");

    const ownership = page.getByTestId("intake-v6-finish-ownership-note");
    await expect(ownership).toBeVisible();
    await expect(ownership).toHaveAttribute("data-expanded", "false");

    const primaryPanel = page.getByTestId("intake-v6-review-tab-panel-finisaje");
    const primaryText = await primaryPanel.innerText();
    // Collapsed: no raw tokens in primary chrome
    expect(primaryText).not.toMatch(/SURFACE_FINISH/);
    expect(primaryText).not.toMatch(/RETURN-CANT/);
    expect(primaryText).not.toMatch(/OWNER_GATE_REQUIRED/);
    expect(primaryText).toMatch(/Detalii tehnice despre finisaj/i);
    expect(primaryText).toMatch(/Finisaje pe layer/i);

    await shot(page, "06_technical_details_collapsed.png");
    await shot(page, "08_no_raw_token_primary.png");

    await page.getByTestId("intake-v6-finish-ownership-note-toggle").click();
    await expect(ownership).toHaveAttribute("data-expanded", "true");
    await expect(page.getByTestId("intake-v6-finish-ownership-technical-tokens")).toBeVisible();
    const tech = await page.getByTestId("intake-v6-finish-ownership-technical-tokens").innerText();
    expect(tech).toMatch(/SURFACE_FINISH/);
    await shot(page, "07_technical_details_expanded.png");
    await shot(page, "05_confirmed_or_configured_finish.png");

    // Incomplete / actionable: layer section still present
    await expect(page.getByTestId("intake-v6-review-section-face-letters")).toBeVisible();
    await shot(page, "03_incomplete_or_controls_visible.png");

    // Tab structure unchanged
    await expect(page.getByTestId("intake-v6-review-tab-finisaje")).toBeVisible();
    await expect(page.getByTestId("intake-v6-review-tab-iluminare")).toBeVisible();
    await expect(page.getByTestId("intake-v6-review-tab-montaj")).toBeVisible();
    await shot(page, "11_page2_tab_structure.png");

    // Montaj IA frozen
    await page.getByTestId("intake-v6-review-tab-montaj").click();
    await expect(page.getByTestId("intake-v6-fundal-carcasa-cluster")).toBeVisible();
    await expect(page.getByTestId("intake-v6-montaj-commercial-cluster")).toBeVisible();
    await expect(page.getByTestId("intake-v6-montaj-advanced-cluster")).toBeVisible();
    await shot(page, "12_montaj_regression_check.png");

    await page.reload({ waitUntil: "domcontentloaded" });
    await waitAuth(page);
    await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 90_000 });
    await page.getByTestId("intake-v6-review-tab-finisaje").click();
    await expect(page.getByTestId("intake-v6-finish-ownership-note")).toHaveAttribute(
      "data-expanded",
      "false",
    );
    const reloadedPrimary = await page.getByTestId("intake-v6-review-tab-panel-finisaje").innerText();
    expect(reloadedPrimary).not.toMatch(/SURFACE_FINISH/);
    await shot(page, "09_reloaded_state.png");

    fs.writeFileSync(
      path.join(OUT, "..", "e2e_run.json"),
      JSON.stringify({ workspace: ws, ui: UI, backend: BACKEND, svg: path.basename(SVG) }, null, 2),
      "utf8",
    );
  });
});
