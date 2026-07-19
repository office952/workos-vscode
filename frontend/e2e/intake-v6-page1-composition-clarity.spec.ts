/**
 * Live Page 1 + composition clarity: no pseudo fill in primary UI,
 * handoff summary, composition concise, Montaj IA untouched.
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
  "intake-v6-page1-composition-clarity-2026-07-19",
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

test.describe("Intake V6 Page 1 composition clarity", () => {
  test.use({ viewport: { width: 1440, height: 960 } });

  test("operator labels, handoff, composition, Page2 Montaj frozen", async ({ page }) => {
    test.setTimeout(300_000);
    expect(fs.existsSync(SVG)).toBe(true);
    const ws = await createWorkspace(`page1-clarity-${Date.now()}`);

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
      await page.waitForTimeout(1000);
    }

    await shot(page, "01_page1_initial_analysis.png");
    await shot(page, "15_full_page1.png");

    // Open inspect legend — primary titles must not show pseudo fill
    const inspectOpen = page.getByTestId("intake-v6-open-preview-inspect");
    if (await inspectOpen.isVisible().catch(() => false)) {
      await inspectOpen.click();
      await expect(page.getByTestId("intake-v6-preview-inspect-dialog")).toBeVisible({
        timeout: 15_000,
      });
      const legendText = await page.getByTestId("intake-v6-layer-legend").innerText();
      expect(legendText).not.toMatch(/pseudo fill/i);
      expect(legendText).toMatch(/Element \d+/i);
      await shot(page, "02_detected_elements_legend.png");
      const dialog = page.getByTestId("intake-v6-preview-inspect-dialog");
      const closeBtn = dialog.getByRole("button", { name: /^Close$/i });
      await closeBtn.click();
      await expect(dialog).toBeHidden({ timeout: 10_000 });
    }

    await shot(page, "03_proposed_role_cards.png");

    const techDetails = page
      .getByRole("button", { name: /Detalii tehnice analiză/i })
      .or(page.locator("summary", { hasText: /Detalii tehnice/i }))
      .first();
    if (await techDetails.isVisible().catch(() => false)) {
      await shot(page, "06_technical_diagnostics_collapsed.png");
      await techDetails.click();
      await page.waitForTimeout(300);
      await shot(page, "07_technical_diagnostics_expanded.png");
    }

    // Assign Contur suport on ACM layer when possible
    const roleSelects = page.locator('[data-testid^="intake-v6-layer-role-"]');
    await roleSelects.first().waitFor({ state: "attached", timeout: 60_000 });
    const count = await roleSelects.count();
    for (let i = 0; i < count; i += 1) {
      const sel = roleSelects.nth(i);
      const testId = (await sel.getAttribute("data-testid")) || "";
      const html = await sel.innerHTML().catch(() => "");
      if (!/support_panel|Contur suport/i.test(html)) continue;
      if (!/gravare|fundal|acm|alucobond|support|panel|cnc-135/i.test(testId)) continue;
      await sel.selectOption("support_panel").catch(async () => {
        const opts = await sel.locator("option").allTextContents();
        const label = opts.find((o) => /contur suport/i.test(o));
        if (label) await sel.selectOption({ label });
      });
      await page.waitForTimeout(2000);
      break;
    }

    const cardsText = await page.getByTestId("intake-v6-layer-table").innerText().catch(async () =>
      page.locator("body").innerText(),
    );
    expect(cardsText).not.toMatch(/pseudo fill-/i);

    await shot(page, "05_unresolved_or_attention.png");

    const handoff = page.getByTestId("intake-v6-page1-handoff-summary");
    await expect(handoff).toBeVisible();
    await shot(page, "10_page1_blocked_or_pending_summary.png");

    const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
    if (await confirmAll.isVisible().catch(() => false)) {
      await confirmAll.click();
      await page.waitForTimeout(1500);
    }
    if (await confirmAll.isVisible().catch(() => false)) {
      await confirmAll.click();
      await page.waitForTimeout(1000);
    }

    await expect(page.getByTestId("intake-v6-layers-all-confirmed")).toBeVisible({
      timeout: 30_000,
    });
    await expect(handoff).toBeVisible();
    await expect(handoff).toContainText(/Pagina 2|configura/i);
    await shot(page, "04_confirmed_role.png");
    await shot(page, "09_page1_ready_summary.png");

    // Composition — concise primary
    const composition = page.getByTestId("intake-v6-product-composition-panel");
    if (await composition.count()) {
      const compText = await composition.innerText();
      expect(compText).not.toMatch(/SURFACE_FINISH|OWNER_GATE/);
      await shot(page, "08_composition_on_page1.png");
    }

    await expect(page.getByTestId("intake-v6-footer-next")).toBeEnabled({ timeout: 90_000 });
    await page.getByTestId("intake-v6-footer-next").click();
    await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 90_000 });

    await shot(page, "11_page2_composition_summary.png");
    const page2Comp = page.getByTestId("intake-v6-product-composition-panel");
    if (await page2Comp.count()) {
      // Confirmed or issues — should not dump ownership prose
      const t = await page2Comp.innerText();
      expect(t).not.toMatch(/SURFACE_FINISH/);
    }

    await shot(page, "12_page2_sticky_blocker.png");

    // Montaj IA frozen checks
    await page.getByTestId("intake-v6-review-tab-montaj").click();
    await expect(page.getByTestId("intake-v6-review-tab-panel-montaj")).toBeVisible();
    await expect(page.getByTestId("intake-v6-fundal-carcasa-cluster")).toBeVisible();
    await expect(page.getByTestId("intake-v6-montaj-commercial-cluster")).toBeVisible();
    await expect(page.getByTestId("intake-v6-montaj-advanced-cluster")).toBeVisible();
    await shot(page, "13_segmented_handoff_montaj.png");

    // Reload preserves roles
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitAuth(page);
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 90_000 });
    await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 90_000 });
    await page.getByTestId("intake-v6-review-tab-montaj").click();
    await expect(page.getByTestId("intake-v6-fundal-carcasa-cluster")).toBeVisible({ timeout: 30_000 });
    await shot(page, "14_reloaded_state.png");

    fs.writeFileSync(
      path.join(OUT, "..", "e2e_run.json"),
      JSON.stringify({ workspace: ws, ui: UI, backend: BACKEND, svg: path.basename(SVG) }, null, 2),
      "utf8",
    );
  });
});
