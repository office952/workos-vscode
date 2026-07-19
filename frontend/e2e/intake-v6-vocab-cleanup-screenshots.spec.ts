/**
 * Live screenshot pack for vocabulary / mounting noise cleanup.
 * FE :3001 · BE :8003 · real Desktop SVG.
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
  "intake-v6-vocabulary-residual-ui-cleanup-2026-07-19",
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

test.describe("Intake V6 vocab cleanup screenshots", () => {
  test.use({ viewport: { width: 1440, height: 960 } });

  test("captures Page 2 Montaj vocabulary states", async ({ page }) => {
    test.setTimeout(300_000);
    expect(fs.existsSync(SVG)).toBe(true);
    const ws = await createWorkspace(`vocab-shots-${Date.now()}`);

    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    await waitAuth(page);
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 90_000 });

    await page.getByTestId("intake-v6-svg-input").setInputFiles(SVG);
    await expect(page.getByTestId("intake-v6-file-confirm-chip")).toBeVisible({ timeout: 90_000 });

    // Wait analysis
    const started = Date.now();
    while (Date.now() - started < 60_000) {
      const snap = await getWorkspace(ws.id);
      if (snap?.payload?.svg_analysis_json) break;
      await page.waitForTimeout(1000);
    }

    // Assign Contur suport on ACM/fundal layer
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
      await page.waitForTimeout(2500);
      break;
    }

    const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
    if (await confirmAll.isVisible().catch(() => false)) {
      await confirmAll.click();
      await page.waitForTimeout(1500);
    }
    if (await confirmAll.isVisible().catch(() => false)) {
      await confirmAll.click();
      await page.waitForTimeout(1000);
    }

    await expect(page.getByTestId("intake-v6-footer-next")).toBeEnabled({ timeout: 90_000 });
    await page.getByTestId("intake-v6-footer-next").click();
    await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 90_000 });

    await shot(page, "01_page2_tab_labels.png");

    const iluminare = page.getByTestId("intake-v6-review-tab-iluminare");
    if (await iluminare.count()) {
      await iluminare.click();
      await page.waitForTimeout(600);
    }
    await shot(page, "02_iluminare_si_surse.png");

    const montaj = page.getByTestId("intake-v6-review-tab-montaj");
    await montaj.click();
    await expect(page.getByTestId("intake-v6-review-tab-panel-montaj")).toBeVisible({
      timeout: 30_000,
    });
    await page.waitForTimeout(1500);

    await shot(page, "03_fundal_si_carcasa.png");

    const commercial = page.getByTestId("intake-v6-montaj-commercial-cluster");
    await expect(commercial).toBeVisible({ timeout: 15_000 });
    const commercialToggle = page.getByTestId("intake-v6-montaj-commercial-cluster-toggle");
    if ((await commercial.getAttribute("data-expanded")) === "true") {
      await commercialToggle.click();
      await page.waitForTimeout(300);
    }
    await shot(page, "04_montaj_comercial_collapsed.png");
    await commercialToggle.click();
    await page.waitForTimeout(400);
    await expect(page.getByTestId("intake-v6-mounting-site-section")).toBeVisible();
    await shot(page, "05_montaj_comercial_expanded.png");

    const advanced = page.getByTestId("intake-v6-montaj-advanced-cluster");
    const advancedToggle = page.getByTestId("intake-v6-montaj-advanced-cluster-toggle");
    if ((await advanced.getAttribute("data-expanded")) === "true") {
      await advancedToggle.click();
      await page.waitForTimeout(300);
    }
    await shot(page, "06_avansat_collapsed.png");
    await advancedToggle.click();
    await page.waitForTimeout(400);
    await shot(page, "07_avansat_diagnostics_raw.png");

    // Owner / ACP readiness if present
    const readiness = page.getByTestId("intake-v6-acp-module-readiness").first();
    if (await readiness.count()) {
      await readiness.scrollIntoViewIfNeeded();
      const text = await readiness.innerText();
      expect(text).not.toMatch(/OWNER_GATE/);
      expect(text).toMatch(/Necesită|Pregătit|Confirm|configurare/i);
    }
    await shot(page, "08_owner_decision_primary.png");

    await page
      .getByTestId("intake-v6-review-operator-blocker-banner")
      .first()
      .scrollIntoViewIfNeeded()
      .catch(() => undefined);
    await shot(page, "09_sticky_blocker_summary.png");

    // Confirm segmented if button present
    const confirmSeg = page
      .getByTestId("intake-v6-segmented-confirm")
      .or(page.getByRole("button", { name: /Confirmă ansamblu|Confirmă segment/i }))
      .first();
    if (await confirmSeg.isVisible().catch(() => false)) {
      await confirmSeg.click();
      await page.waitForTimeout(2500);
    }
    await shot(page, "10_segmented_confirmed_or_proposal.png");

    const elec = page.getByTestId("intake-v6-segmented-electrical-panel").first();
    if (await elec.count()) {
      await elec.scrollIntoViewIfNeeded();
      const elecText = await elec.innerText();
      expect(elecText).not.toMatch(/\bOWNER_GATE\b/);
      expect(elecText).not.toMatch(/\bSHARED_FROM_PANEL\b/);
    }
    await shot(page, "11_electrical_panel.png");

    await shot(page, "12_final_confirmation_footer.png");
    await shot(page, "13_full_montaj_page.png");

    // Primary montaj panel must not show OWNER_GATE
    const montajText = await page.getByTestId("intake-v6-review-tab-panel-montaj").innerText();
    // Allow advanced ownership notes which use MOUNTING tokens but not OWNER_GATE_REQUIRED
    const primaryWithoutAdvanced = montajText.replace(
      /Ownership:[\s\S]*?chip sold[\s\S]*?țintă\./g,
      "",
    );
    expect(primaryWithoutAdvanced).not.toMatch(/OWNER_GATE_REQUIRED|PROFILE_INITIAL_SET_OWNER_GATE/);

    // Site section nested under commercial cluster in DOM
    const siteInside = await page.evaluate(() => {
      const commercial = document.querySelector('[data-testid="intake-v6-montaj-commercial-cluster"]');
      const site = document.querySelector('[data-testid="intake-v6-mounting-site-section"]');
      return Boolean(commercial && site && commercial.contains(site));
    });
    expect(siteInside).toBe(true);

    fs.writeFileSync(
      path.join(OUT, "..", "screenshot_run.json"),
      JSON.stringify(
        {
          workspace: ws,
          ui: UI,
          backend: BACKEND,
          svg: path.basename(SVG),
          siteInsideCommercial: siteInside,
        },
        null,
        2,
      ),
      "utf8",
    );
  });
});
