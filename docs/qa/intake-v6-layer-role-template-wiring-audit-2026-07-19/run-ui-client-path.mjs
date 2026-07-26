/**
 * Client-path UI walk: file chooser → analyzer → roles → Page 2.
 * Complements server-upload walker (which does not hydrate Page 1 SVG UI).
 */
import fs from "fs";
import path from "path";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const API = `${UI}/api/v1/intake-v6`;
const OUT = path.join(__dirname, "runtime");
const SHOTS = path.join(__dirname, "screenshots");
const FIX = "C:/Users/offic/Desktop/fisiere-teste-svg";

const fixtures = [
  { id: "acm_segmented", file: "litere-cu-fundal-acm-segmentat.svg" },
  { id: "acm_crossing", file: "litere-cu-fundal-acm-segmentat-litera-peste-imbinare.svg" },
  { id: "simple_letters", file: "litere-vol-1-layer.svg" },
];

async function createWs(title) {
  const r = await fetch(`${API}/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      selected_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      analyzer_mode: "analyzer_first",
    }),
  });
  return r.json();
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const results = [];

  for (const f of fixtures) {
    const ws = await createWs(`ui-wiring-${f.id}-${Date.now()}`);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, {
      waitUntil: "domcontentloaded",
      timeout: 120000,
    });
    await page.waitForTimeout(2000);

    const filePath = path.join(FIX, f.file);
    const chooserPromise = page.waitForEvent("filechooser", { timeout: 15000 }).catch(() => null);
    await page.getByRole("button", { name: /Încarcă SVG/i }).first().click({ force: true }).catch(() => null);
    const chooser = await chooserPromise;
    if (chooser) {
      await chooser.setFiles(filePath);
    } else {
      const input = page.locator('input[type="file"]').first();
      if ((await input.count()) > 0) await input.setInputFiles(filePath);
    }
    await page.waitForTimeout(6000);
    await page.screenshot({
      path: path.join(SHOTS, `${f.id}_ui_01_after_client_upload.png`),
    });

    const probe = await page.evaluate(() => {
      const text = document.body.innerText;
      const roles = [...document.querySelectorAll('select[data-testid^="intake-v6-layer-role-"]')].map(
        (el) => ({
          id: el.getAttribute("data-testid"),
          value: el.value,
          label: el.selectedOptions?.[0]?.textContent || "",
        }),
      );
      return {
        href: location.href,
        roles,
        hasRoleTable: roles.length > 0,
        textSnips: {
          vectorLitere: /Vector Litere/i.test(text),
          vectorLogo: /Vector Logo/i.test(text),
          support: /Contur suport|Fundal \/ suport|Alucobond|Panou Alucobond/i.test(text),
          compositionBlocked: /Nu exista roluri constructive/i.test(text),
        },
        stepLayers: document
          .querySelector('[data-testid="intake-v6-progress-step-layers"]')
          ?.getAttribute("aria-current"),
        stepReview: document
          .querySelector('[data-testid="intake-v6-progress-step-review"]')
          ?.getAttribute("aria-current"),
        stepConfirm: document
          .querySelector('[data-testid="intake-v6-progress-step-confirm"]')
          ?.getAttribute("aria-current"),
        footer: (document.body.innerText.match(/Următorul pas:[^\n]+/) || [])[0] || null,
      };
    });

    let nav = null;
    if (probe.roles.length) {
      const sel = page.locator('select[data-testid^="intake-v6-layer-role-"]').first();
      const before = await page.evaluate(() => ({
        href: location.href,
        confirm: document
          .querySelector('[data-testid="intake-v6-progress-step-confirm"]')
          ?.getAttribute("aria-current"),
        review: document
          .querySelector('[data-testid="intake-v6-progress-step-review"]')
          ?.getAttribute("aria-current"),
        layers: document
          .querySelector('[data-testid="intake-v6-progress-step-layers"]')
          ?.getAttribute("aria-current"),
      }));
      const cur = await sel.inputValue();
      const target = cur === "face" ? "printed_artwork" : "face";
      await sel.selectOption(target).catch(() => null);
      await page.waitForTimeout(1500);
      const after = await page.evaluate(() => ({
        href: location.href,
        confirm: document
          .querySelector('[data-testid="intake-v6-progress-step-confirm"]')
          ?.getAttribute("aria-current"),
        review: document
          .querySelector('[data-testid="intake-v6-progress-step-review"]')
          ?.getAttribute("aria-current"),
        layers: document
          .querySelector('[data-testid="intake-v6-progress-step-layers"]')
          ?.getAttribute("aria-current"),
      }));
      nav = {
        before,
        after,
        from: cur,
        to: target,
        jumpedToConfirm:
          after.confirm === "step" || /step=confirm/.test(after.href || ""),
        jumpedToReview: after.review === "step",
      };
      await page.screenshot({
        path: path.join(SHOTS, `${f.id}_ui_02_after_role_change.png`),
      });
    }

    const saveBtn = page
      .getByRole("button", { name: /Salvează|Continuă la Configurare|Confirmă rolurile/i })
      .first();
    if ((await saveBtn.count()) > 0) {
      await saveBtn.click({ force: true }).catch(() => null);
      await page.waitForTimeout(2500);
    }

    await page.getByTestId("intake-v6-progress-step-review").click({ force: true }).catch(() => null);
    await page.waitForTimeout(1500);
    for (const tab of ["finisaje", "iluminare", "montaj"]) {
      await page.getByTestId(`intake-v6-review-tab-${tab}`).click({ force: true }).catch(() => null);
      await page.waitForTimeout(700);
      await page.screenshot({ path: path.join(SHOTS, `${f.id}_ui_03_${tab}.png`) });
    }

    const page2 = await page.evaluate(() => {
      const t = document.body.innerText;
      return {
        href: location.href,
        letterCluster: !!document.querySelector(
          '[data-testid="intake-v6-letter-group-face-finishes"]',
        ),
        artwork: !!document.querySelector('[data-testid="intake-v6-artwork-finishes"]'),
        lighting: !!document.querySelector('[data-testid="intake-v6-review-lighting-section"]'),
        montajPanel: !!document.querySelector('[data-testid="intake-v6-review-tab-panel-montaj"]'),
        oracal: /Oracal/i.test(t),
        folds: /pliere|fold|L1|L2|adâncime caset|casetat/i.test(t),
        segmented: /segment|panouri|îmbinare/i.test(t),
        alucobond: /Alucobond|ACM|ACP/i.test(t),
      };
    });

    const api = await (await fetch(`${API}/workspaces/${ws.id}`)).json();
    const finish = api.payload?.finish_setup || {};
    const bindings = (finish.svg_component_bindings || []).map((b) => ({
      role: b.geometry_role,
      tpl: b.component_template_code,
      status: b.status,
      layers: b.selected_geometry?.layer_ids,
    }));
    const roles = (api.payload?.layer_role_setup?.layers || []).map((l) => ({
      key: l.layer_key,
      auto: l.auto_role,
      conf: l.confirmed_role,
      state: l.confirmation_state,
    }));
    const result = {
      fixture: f,
      workspace_id: ws.id,
      probe,
      nav,
      page2,
      bindings,
      roles,
      readiness: api.readiness_status,
      composition_status: api.payload?.product_composition_recommendation?.status,
      composition_items: (api.payload?.product_composition_recommendation?.composition_items || []).map(
        (i) => ({
          label: i.display_name,
          template: i.template_code || i.component_template_code,
        }),
      ),
      seg: finish.segmented_background?.status || null,
      support: finish.svg_support_selection?.status || null,
    };
    fs.writeFileSync(path.join(OUT, `${f.id}_ui_client_path.json`), JSON.stringify(result, null, 2));
    results.push(result);
    console.log(
      JSON.stringify(
        {
          id: f.id,
          roles: probe.roles,
          nav,
          bindings,
          page2,
          readiness: api.readiness_status,
        },
        null,
        2,
      ),
    );
    await page.close();
  }

  const known = "bd26e3d5-1e63-4e39-8e72-ebaaea501e49";
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto(`${UI}/intake-v6/${known}/operator`, {
    waitUntil: "domcontentloaded",
    timeout: 120000,
  });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(SHOTS, "known_wired_01_page1.png") });
  await page.getByTestId("intake-v6-progress-step-review").click({ force: true }).catch(() => null);
  await page.waitForTimeout(1200);
  for (const tab of ["finisaje", "iluminare", "montaj"]) {
    await page.getByTestId(`intake-v6-review-tab-${tab}`).click({ force: true }).catch(() => null);
    await page.waitForTimeout(800);
    await page.screenshot({ path: path.join(SHOTS, `known_wired_02_${tab}.png`) });
  }
  const knownProbe = await page.evaluate(() => {
    const t = document.body.innerText;
    return {
      href: location.href,
      letterCluster: !!document.querySelector(
        '[data-testid="intake-v6-letter-group-face-finishes"]',
      ),
      artwork: !!document.querySelector('[data-testid="intake-v6-artwork-finishes"]'),
      lighting: !!document.querySelector('[data-testid="intake-v6-review-lighting-section"]'),
      montaj: !!document.querySelector('[data-testid="intake-v6-review-tab-panel-montaj"]'),
      oracal: /Oracal/i.test(t),
      folds: /pliere|fold|L1|L2|adâncime caset|casetat/i.test(t),
      segmented: /segment|panouri|îmbinare/i.test(t),
      alucobond: /Alucobond|ACM|ACP|Panou Alucobond/i.test(t),
      vectorLitere: /Vector Litere|Litere volumetrice/i.test(t),
    };
  });
  const knownApi = await (await fetch(`${API}/workspaces/${known}`)).json();
  fs.writeFileSync(
    path.join(OUT, "known_wired_ui_probe.json"),
    JSON.stringify(
      {
        knownProbe,
        bindings: knownApi.payload?.finish_setup?.svg_component_bindings,
        roles: knownApi.payload?.layer_role_setup?.layers,
        composition: knownApi.payload?.product_composition_recommendation,
        seg: knownApi.payload?.finish_setup?.segmented_background,
      },
      null,
      2,
    ),
  );
  console.log("known", JSON.stringify(knownProbe, null, 2));
  await page.close();
  await browser.close();
  fs.writeFileSync(
    path.join(OUT, "ui_client_path_summary.json"),
    JSON.stringify({ at: new Date().toISOString(), ui: UI, results, knownProbe }, null, 2),
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
