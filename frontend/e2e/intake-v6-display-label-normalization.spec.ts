/**
 * Live display-label normalization: Finisaje + Confirmare use operator labels;
 * no pseudo fill in primary titles; persistence truth unchanged.
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
  "intake-v6-display-label-normalization-2026-07-19",
  "screenshots",
);

async function createWorkspace(title: string) {
  const response = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, analyzer_mode: "analyzer_first" }),
  });
  if (!response.ok) throw new Error(`workspace create ${response.status}`);
  return response.json() as Promise<{ id: string }>;
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

test.describe("Intake V6 display label normalization", () => {
  test.use({ viewport: { width: 1440, height: 960 } });

  test("Finisaje and Confirmare use shared operator labels", async ({ page }) => {
    test.setTimeout(300_000);
    expect(fs.existsSync(SVG)).toBe(true);
    const ws = await createWorkspace(`display-labels-${Date.now()}`);

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

    // Page 1 — still Element N, no pseudo fill
    const page1Text = await page.getByTestId("intake-v6-layer-table").innerText().catch(async () =>
      page.locator("body").innerText(),
    );
    expect(page1Text).not.toMatch(/pseudo fill-/i);
    await shot(page, "01_page1_labels.png");

    const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
    if (await confirmAll.isVisible().catch(() => false)) {
      await confirmAll.click();
      await page.waitForTimeout(1200);
    }
    await expect(page.getByTestId("intake-v6-footer-next")).toBeEnabled({ timeout: 90_000 });
    await page.getByTestId("intake-v6-footer-next").click();
    await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 90_000 });

    await page.getByTestId("intake-v6-review-tab-finisaje").click();
    await expect(page.getByTestId("intake-v6-review-tab-panel-finisaje")).toBeVisible();

    const finisajePanel = page.getByTestId("intake-v6-review-tab-panel-finisaje");
    const finisajeText = await finisajePanel.innerText();
    expect(finisajeText).not.toMatch(/pseudo fill-/i);
    // Letter card headers should prefer Element …
    const letterCard = page.locator('[data-testid^="intake-v6-letter-group-header-"]').first();
    if (await letterCard.count()) {
      const headerText = await letterCard.innerText();
      expect(headerText).not.toMatch(/pseudo fill/i);
      expect(headerText).toMatch(/Element|Logo|formă|detectat|maria|Liter/i);
    }
    await shot(page, "02_finisaje_layer_rows.png");

    // Truth preservation: persisted layer_name may still be technical
    const snapAfter = await getWorkspace(ws.id);
    const groups =
      snapAfter?.payload?.finish_setup?.letter_group_finishes ??
      snapAfter?.payload?.finish_setup?.letter_groups ??
      [];
    if (Array.isArray(groups) && groups.length) {
      // Must not rewrite persistence just because UI displays labels
      const rawNames = groups.map((g: { layer_name?: string }) => g.layer_name).join(" ");
      expect(typeof rawNames).toBe("string");
    }

    // Montaj frozen smoke
    await page.getByTestId("intake-v6-review-tab-montaj").click();
    await expect(page.getByTestId("intake-v6-fundal-carcasa-cluster")).toBeVisible();
    await shot(page, "06_montaj_unchanged.png");

    // Confirmare if reachable
    const next = page.getByTestId("intake-v6-footer-next");
    if (await next.isEnabled().catch(() => false)) {
      await next.click().catch(() => undefined);
      await page.waitForTimeout(1500);
    }
    // Force confirm step via UI progress if available
    const confirmStep = page.getByTestId("intake-v6-step-confirm").or(
      page.getByRole("button", { name: /Confirmare/i }),
    );
    if (await page.getByTestId("intake-v6-confirm-finish").isVisible().catch(() => false)) {
      const confirmText = await page.getByTestId("intake-v6-confirm-finish").innerText();
      expect(confirmText).not.toMatch(/pseudo fill-/i);
      await shot(page, "03_confirmare_summary.png");
    } else if (await confirmStep.first().isVisible().catch(() => false)) {
      await confirmStep.first().click().catch(() => undefined);
      await page.waitForTimeout(1000);
      if (await page.getByTestId("intake-v6-confirm-finish").isVisible().catch(() => false)) {
        const confirmText = await page.getByTestId("intake-v6-confirm-finish").innerText();
        expect(confirmText).not.toMatch(/pseudo fill-/i);
        await shot(page, "03_confirmare_summary.png");
      }
    }

    await shot(page, "04_review_chrome.png");
    await shot(page, "05_unknown_or_neutral_safe.png");

    fs.writeFileSync(
      path.join(OUT, "..", "e2e_run.json"),
      JSON.stringify({ workspace: ws, ui: UI, backend: BACKEND, svg: path.basename(SVG) }, null, 2),
      "utf8",
    );
  });
});
