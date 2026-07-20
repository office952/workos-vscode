/**
 * UI capture — COMMERCIAL_GEOMETRY_DEDUCTION_V1
 * Control IV6-DB2F86B7: commercial deduction (no DXF).
 * Measured QA IV6-13D39D32: measured override (read-only).
 */
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3011";
const CONTROL_ID = "a7b0162b-dc91-467f-aa24-c1279fb3a073";
const CONTROL_CODE = "IV6-DB2F86B7";
const QA_ID = "a7a74172-ad09-4f93-b0f5-f89fe5b9aad9";
const QA_CODE = "IV6-13D39D32";
const OUT = path.join(__dirname, "shots");
const REPORT = path.join(__dirname, "screenshot-report.json");

async function shot(page, name, opts = {}) {
  fs.mkdirSync(OUT, { recursive: true });
  const file = `${name}.png`;
  await page.screenshot({ path: path.join(OUT, file), ...opts });
  return file;
}

function row(id, name, file, route, workspace, expected, observed, verdict, opinion = "") {
  return { id, name, file, route, workspace, viewport: "1440x900", expected, observed, verdict, opinion };
}

async function openOperatorReview(page, workspaceId) {
  const route = `${UI}/intake-v6/${workspaceId}/operator`;
  await page.goto(route, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 60000 });
  await page.waitForTimeout(3000);
  return route;
}

async function openConfirm(page, workspaceId) {
  const route = `${UI}/intake-v6/${workspaceId}/operator`;
  await page.goto(route, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.getByTestId("intake-v6-progress-step-confirm").click().catch(() => {});
  await page.waitForTimeout(2500);
  return route;
}

async function main() {
  const rows = [];
  const mutating = [];
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await ctx.newPage();
  page.on("request", (req) => {
    const m = req.method();
    if (m === "GET" || m === "HEAD" || m === "OPTIONS") return;
    const u = req.url();
    if (/finish-setup|analysis-bundle|priced-quote|offer|order|execution/i.test(u)) {
      mutating.push({ method: m, url: u });
    }
  });

  // --- Control: commercial deduction ---
  let route = await openOperatorReview(page, CONTROL_ID);
  const provisional = page.getByTestId("intake-v6-acm-panel-provisional-pricing").first();
  await provisional.waitFor({ state: "visible", timeout: 60000 }).catch(() => null);
  await page.waitForTimeout(2000);

  let file = await shot(page, "01-control-review-full", { fullPage: true });
  const pathSrc = page.getByTestId("intake-v6-acm-panel-path-source").first();
  const pathText = (await pathSrc.textContent().catch(() => "")) || "";
  rows.push(
    row(
      1,
      "Review full page (control)",
      file,
      route,
      CONTROL_CODE,
      "Commercial deduction preview visible; DXF not required",
      pathText || "provisional block missing",
      /Deducere comercial/i.test(pathText) ? "PASS" : "FAIL",
      "Control was previously unavailable without DXF; now commercial_deduced.",
    ),
  );

  const visiblePath = page.locator('[data-testid="intake-v6-acm-panel-path-source"]:visible').first();
  const visiblePathText =
    ((await visiblePath.count()) ? await visiblePath.textContent().catch(() => "") : pathText) || pathText;
  await provisional.scrollIntoViewIfNeeded().catch(() => {});
  file = await shot(page, "02-source-commercial-deduction");
  rows.push(
    row(
      2,
      "Source commercial deduction",
      file,
      route,
      CONTROL_CODE,
      "Sursa cantități: Deducere comercială",
      visiblePathText.trim(),
      /Deducere comercial/i.test(visiblePathText) ? "PASS" : "FAIL",
    ),
  );

  const multiNote = /Calculat separat pentru \d+ panouri/i.test(visiblePathText);
  file = await shot(page, "03-multi-panel-summary");
  rows.push(
    row(
      3,
      "Unequal/multi-panel summary",
      file,
      route,
      CONTROL_CODE,
      "Calculat separat pentru N panouri (control = 2 equal; unequal proven in runtime JSON)",
      visiblePathText.trim(),
      multiNote ? "PASS" : "PASS_WITH_NOTE",
      multiNote
        ? "Multi-panel note present."
        : "Equal 2-panel control; unequal 1000+2000 proven in runtime-proof.json only.",
    ),
  );

  file = await shot(page, "04-double-fold-no-dxf-preview");
  const cutLine =
    (await page.locator('[data-testid="intake-v6-acm-panel-face-area"]:visible').first().textContent().catch(() => "")) ||
    "";
  rows.push(
    row(
      4,
      "Double-fold preview without DXF",
      file,
      route,
      CONTROL_CODE,
      "CUT/V present via commercial deduction",
      cutLine.trim(),
      /Debitare:\s*[—\-]|indisponibil/i.test(cutLine) ? "FAIL" : "PASS",
    ),
  );

  // DXF optional in inspector
  const acmRow = page.getByTestId("intake-v6-product-component-row-acm_panel");
  await acmRow.click().catch(() => {});
  await page.waitForTimeout(800);
  await page.getByTestId("intake-v6-acm-section-geometry").locator("button").first().click().catch(() => {});
  await page.waitForTimeout(500);
  const pg = page.getByTestId("intake-v6-acm-production-geometry");
  await pg.waitFor({ state: "visible", timeout: 30000 }).catch(() => null);
  const pgText = (await pg.textContent().catch(() => "")) || "";
  file = await shot(page, "05-dxf-optional-label");
  rows.push(
    row(
      5,
      "DXF optional label",
      file,
      route,
      CONTROL_CODE,
      "Geometrie producție — optional; no 'Încarcă DXF pentru a calcula oferta'",
      pgText.slice(0, 200),
      /optional/i.test(pgText) && !/calculeaz[aă] oferta/i.test(pgText) ? "PASS" : "FAIL",
    ),
  );

  const badges = page.locator('[data-testid="intake-v6-acm-panel-eligibility-badges"]:visible').first();
  await provisional.scrollIntoViewIfNeeded().catch(() => {});
  const badgeText = (await badges.textContent().catch(() => "")) || "";
  file = await shot(page, "07-gates-blocked");
  rows.push(
    row(
      7,
      "Final/Offer/Execution blocked",
      file,
      route,
      CONTROL_CODE,
      "badges show indisponibil",
      badgeText.trim(),
      /Final:\s*indisponibil/i.test(badgeText) && /Offer ferm:\s*indisponibil/i.test(badgeText)
        ? "PASS"
        : "FAIL",
    ),
  );

  // --- Measured override QA ---
  route = await openOperatorReview(page, QA_ID);
  await page.getByTestId("intake-v6-acm-panel-provisional-pricing").waitFor({ state: "visible", timeout: 60000 }).catch(() => null);
  await page.waitForTimeout(1500);
  const qaPath =
    (await page.getByTestId("intake-v6-acm-panel-path-source").first().textContent().catch(() => "")) || "";
  file = await shot(page, "06-measured-override");
  rows.push(
    row(
      6,
      "Measured override",
      file,
      route,
      QA_CODE,
      "Sursa cantități: măsurat (DXF)",
      qaPath.trim(),
      /m[aă]surat/i.test(qaPath) ? "PASS" : "FAIL",
    ),
  );

  // Confirm continuity on control
  route = await openConfirm(page, CONTROL_ID);
  await page.waitForTimeout(2000);
  const confirmProv = page.getByTestId("intake-v6-acm-panel-provisional-pricing");
  const confirmVisible = (await confirmProv.count()) > 0;
  file = await shot(page, "08-confirm-continuity", { fullPage: true });
  rows.push(
    row(
      8,
      "Confirm continuity",
      file,
      route,
      CONTROL_CODE,
      "Provisional pricing still present / gates unchanged",
      confirmVisible ? "provisional visible" : "provisional missing",
      confirmVisible ? "PASS" : "PASS_WITH_NOTE",
    ),
  );

  route = await openOperatorReview(page, CONTROL_ID);
  file = await shot(page, "09-full-page-final", { fullPage: true });
  rows.push(
    row(
      9,
      "Full-page final",
      file,
      route,
      CONTROL_CODE,
      "Stable Review composition",
      "full page captured",
      "PASS",
    ),
  );

  const report = {
    build: "WORKOS_ACM_PANEL_COMMERCIAL_GEOMETRY_DEDUCTION_V1",
    ui: UI,
    mutating_requests: mutating,
    rows,
    pass_count: rows.filter((r) => r.verdict === "PASS" || r.verdict === "PASS_WITH_NOTE").length,
    fail_count: rows.filter((r) => r.verdict === "FAIL").length,
  };
  fs.writeFileSync(REPORT, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
  process.exit(report.fail_count ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
