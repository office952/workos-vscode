/**
 * Runtime proof — WORKOS_ACM_PANEL_BLUEPRINT_LEVEL_1_PROVISIONAL_S0_S2
 * Fixture IV6-DB2F86B7 @ 1440×900 — zero-write expand/collapse
 */
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const BACKEND = process.env.PW_BACKEND_URL ?? "http://127.0.0.1:8003";
const ID = "a7b0162b-dc91-467f-aa24-c1279fb3a073";
const OUT = __dirname;

async function main() {
  fs.mkdirSync(path.join(OUT, "shots"), { recursive: true });
  const puts = [];
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await ctx.newPage();
  page.on("request", (req) => {
    if (req.method() === "PUT" && /finish-setup/.test(req.url())) {
      puts.push({ t: Date.now(), url: req.url(), phase: page._phase || "?" });
    }
  });

  await page.goto(`${UI}/intake-v6/${ID}/operator`, {
    waitUntil: "domcontentloaded",
    timeout: 120000,
  });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 60000 });

  await page.screenshot({
    path: path.join(OUT, "shots", "01-configurare-full.png"),
    fullPage: true,
  });

  await page.getByTestId("intake-v6-product-component-row-acm_panel").click();
  await page.waitForTimeout(500);

  const preview = page.getByTestId("intake-v6-acm-blueprint-preview");
  await preview.waitFor({ state: "visible", timeout: 15000 });

  const readiness = await preview.getAttribute("data-readiness");
  const expanded0 = await preview.getAttribute("data-expanded");
  const summary = await page.getByTestId("intake-v6-acm-blueprint-collapsed-summary").innerText();

  await page.screenshot({
    path: path.join(OUT, "shots", "02-inspector-collapsed-preview.png"),
  });

  page._phase = "expand";
  const putsBefore = puts.length;
  await page.getByTestId("intake-v6-acm-blueprint-toggle").click();
  await page.waitForTimeout(300);

  const svg = page.getByTestId("intake-v6-acm-blueprint-front-svg");
  await svg.waitFor({ state: "visible", timeout: 5000 });
  const aw = await svg.getAttribute("data-assembly-width");
  const ah = await svg.getAttribute("data-assembly-height");
  const overall = await page
    .getByTestId("intake-v6-acm-blueprint-overall-label")
    .evaluate((el) => el.textContent?.trim() ?? "");
  const disclaimer = await page
    .getByTestId("intake-v6-acm-blueprint-disclaimer")
    .evaluate((el) => el.textContent?.trim() ?? "");
  const joint = page.getByTestId("intake-v6-acm-blueprint-joint-joint_panel_1_panel_2");
  const jointX = (await joint.count())
    ? await joint.getAttribute("data-joint-x")
    : null;
  const letterUnknown = (await page.getByTestId("intake-v6-acm-blueprint-letter-unknown").count()) > 0;
  const compositionBanner =
    (await page.getByTestId("intake-v6-acm-blueprint-composition-banner").count()) > 0;
  const construction =
    (await page.getByTestId("intake-v6-acm-blueprint-construction").count()) > 0;

  await page.screenshot({
    path: path.join(OUT, "shots", "03-expanded-front.png"),
  });
  await page.locator('[data-testid="intake-v6-acm-blueprint-expanded"]').screenshot({
    path: path.join(OUT, "shots", "04-overall-2000x350.png"),
  }).catch(() => {});

  await page.screenshot({
    path: path.join(OUT, "shots", "05-panels-joint.png"),
  });

  // hover / select panel region (no writes)
  page._phase = "hover";
  await svg.hover();
  await page.waitForTimeout(200);

  page._phase = "construction_scroll";
  if (construction) {
    await page.getByTestId("intake-v6-acm-blueprint-construction").scrollIntoViewIfNeeded();
  }
  await page.screenshot({
    path: path.join(OUT, "shots", "06-construction-section.png"),
  });

  if (compositionBanner) {
    await page.screenshot({
      path: path.join(OUT, "shots", "07-composition-inconsistency.png"),
    });
  }

  await page.screenshot({
    path: path.join(OUT, "shots", "08-disclaimer-relations.png"),
  });

  page._phase = "collapse";
  await page.getByTestId("intake-v6-acm-blueprint-toggle").click();
  await page.waitForTimeout(200);

  page._phase = "reexpand";
  await page.getByTestId("intake-v6-acm-blueprint-toggle").click();
  await page.waitForTimeout(200);

  const putsAfterInteract = puts.length - putsBefore;

  // scroll page
  await page.evaluate(() => window.scrollBy(0, 600));
  await page.waitForTimeout(200);
  await page.screenshot({
    path: path.join(OUT, "shots", "09-scroll.png"),
    fullPage: true,
  });

  // refresh
  page._phase = "refresh";
  const putsBeforeRefresh = puts.length;
  await page.reload({ waitUntil: "domcontentloaded", timeout: 120000 });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 60000 });
  await page.getByTestId("intake-v6-product-component-row-acm_panel").click();
  await page.waitForTimeout(500);
  const preview2 = page.getByTestId("intake-v6-acm-blueprint-preview");
  await preview2.waitFor({ state: "visible", timeout: 15000 });
  const readiness2 = await preview2.getAttribute("data-readiness");
  const summary2 = await page.getByTestId("intake-v6-acm-blueprint-collapsed-summary").innerText();
  await page.getByTestId("intake-v6-acm-blueprint-toggle").click();
  await page.waitForTimeout(300);
  const aw2 = await page.getByTestId("intake-v6-acm-blueprint-front-svg").getAttribute("data-assembly-width");
  await page.screenshot({
    path: path.join(OUT, "shots", "10-after-refresh.png"),
  });

  const putsDuringProof = puts.filter((p) =>
    ["expand", "hover", "construction_scroll", "collapse", "reexpand", "refresh"].includes(
      p.phase,
    ),
  );

  // API sanity
  let apiAssembly = null;
  try {
    const ws = await (await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${ID}`)).json();
    const inst =
      ws.payload?.finish_setup?.acm_panel_instance ??
      ws.payload?.finish_setup?.mounting_solution?.configuration?.acm_panel_instance;
    const panels = inst?.geometry?.panels ?? [];
    const w = panels.reduce((s, p) => Math.max(s, (p.position?.x_mm ?? 0) + (p.width_mm ?? 0)), 0);
    const h = panels.reduce((s, p) => Math.max(s, (p.position?.y_mm ?? 0) + (p.height_mm ?? 0)), 0);
    apiAssembly = { panels: panels.length, width: w, height: h, envelope: inst?.geometry?.width_mm };
  } catch (e) {
    apiAssembly = { error: String(e) };
  }

  const report = {
    workspace: "IV6-DB2F86B7",
    workspaceId: ID,
    viewport: "1440x900",
    readiness,
    readinessAfterRefresh: readiness2,
    collapsedSummary: summary,
    collapsedSummaryAfterRefresh: summary2,
    expandedInitially: expanded0,
    assemblyWidth: aw,
    assemblyHeight: ah,
    assemblyWidthAfterRefresh: aw2,
    overallLabel: overall,
    jointX,
    disclaimer,
    letterUnknown,
    compositionBanner,
    construction,
    putCountDuringBlueprintInteract: putsAfterInteract,
    putCountPhases: putsDuringProof.length,
    puts: putsDuringProof,
    apiAssembly,
    pass:
      readiness === "L1-P" &&
      aw === "2000" &&
      ah === "350" &&
      jointX === "1000" &&
      putsDuringProof.length === 0 &&
      aw2 === "2000" &&
      readiness2 === "L1-P",
  };

  fs.writeFileSync(path.join(OUT, "network-proof.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
  if (!report.pass) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
