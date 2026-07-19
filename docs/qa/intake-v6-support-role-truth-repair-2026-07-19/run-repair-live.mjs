/**
 * Live validation for support role truth repair.
 * Stack: FE :3000 · BE via /api proxy (:8003).
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

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });

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
  if (!r.ok) throw new Error(`create ws ${r.status}`);
  return r.json();
}

async function getWs(id) {
  const r = await fetch(`${API}/workspaces/${id}`);
  return r.json();
}

async function uploadServer(id, filePath) {
  const buf = fs.readFileSync(filePath);
  const form = new FormData();
  form.append("file", new Blob([buf], { type: "image/svg+xml" }), path.basename(filePath));
  const r = await fetch(`${API}/workspaces/${id}/svg`, { method: "POST", body: form });
  return { status: r.status, body: await r.json().catch(() => null) };
}

async function clientUpload(page, filePath) {
  const chooserPromise = page.waitForEvent("filechooser", { timeout: 15000 }).catch(() => null);
  await page.getByRole("button", { name: /Încarcă SVG/i }).first().click({ force: true }).catch(() => null);
  const chooser = await chooserPromise;
  if (chooser) await chooser.setFiles(filePath);
  else {
    const input = page.locator('input[type="file"]').first();
    if ((await input.count()) > 0) await input.setInputFiles(filePath);
  }
  await page.waitForTimeout(7000);
}

async function probeRoles(page) {
  return page.evaluate(() => {
    const text = document.body.innerText;
    const roles = [...document.querySelectorAll('select[data-testid^="intake-v6-layer-role-"]')].map((el) => ({
      id: el.getAttribute("data-testid"),
      value: el.value,
      label: el.selectedOptions?.[0]?.textContent || "",
    }));
    return {
      href: location.href,
      roles,
      empty: Boolean(document.querySelector('[data-testid="intake-v6-empty-analyzer-state"]')),
      supportError: document.querySelector('[data-testid="intake-v6-contur-suport-error"]')?.textContent || null,
      text: {
        vectorLitere: /Vector Litere/i.test(text),
        conturSuport: /Contur suport/i.test(text),
      },
      confirmDisabled: document
        .querySelector('[data-testid="intake-v6-progress-step-confirm"]')
        ?.hasAttribute("disabled"),
      confirmAria: document
        .querySelector('[data-testid="intake-v6-progress-step-confirm"]')
        ?.getAttribute("aria-disabled"),
    };
  });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const summary = { ui: UI, at: new Date().toISOString(), cases: [] };

  // --- Client ACM segmented ---
  {
    const file = path.join(FIX, "litere-cu-fundal-acm-segmentat.svg");
    const ws = await createWs(`repair-acm-${Date.now()}`);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForTimeout(1500);
    await clientUpload(page, file);
    await page.screenshot({ path: path.join(SHOTS, "01_acm_client_initial.png"), fullPage: true });
    const initial = await probeRoles(page);

    // Confirm Contur suport on grey if proposed, else select it
    const supportSel = page.locator('select[data-testid="intake-v6-layer-role-pseudo:fill-c5c6c6"]');
    if ((await supportSel.count()) > 0) {
      await supportSel.selectOption("support_panel");
      await page.waitForTimeout(4000);
    }
    const faceSel = page.locator('select[data-testid="intake-v6-layer-role-pseudo:fill-e31e24"]');
    if ((await faceSel.count()) > 0) {
      await faceSel.selectOption("face");
      await page.waitForTimeout(1500);
    }
    await page.screenshot({ path: path.join(SHOTS, "02_acm_after_role_confirm.png"), fullPage: true });
    const afterConfirm = await probeRoles(page);

    // Reload
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: path.join(SHOTS, "03_acm_reload.png"), fullPage: true });
    const afterReload = await probeRoles(page);
    const api = await getWs(ws.id);
    const finish = api.payload?.finish_setup || {};
    const bindings = finish.svg_component_bindings || [];
    const roles = (api.payload?.layer_role_setup?.layers || []).map((l) => ({
      key: l.layer_key,
      auto: l.auto_role,
      conf: l.confirmed_role,
      state: l.confirmation_state,
    }));

    const caseAcm = {
      id: "acm_client",
      workspace_id: ws.id,
      initial,
      afterConfirm,
      afterReload,
      roles,
      bindings: bindings.map((b) => ({
        role: b.geometry_role,
        template: b.component_template_code,
        status: b.status,
      })),
      supportError: afterConfirm.supportError,
      pass: {
        greyProposedSupportOrSelectable:
          initial.roles.some((r) => r.id?.includes("c5c6c6") && (r.value === "support_panel" || r.label.match(/Contur|suport/i))) ||
          initial.roles.some((r) => r.id?.includes("c5c6c6")),
        greyNotForcedFaceProposal: !initial.roles.every((r) => r.value === "face"),
        supportBinding: bindings.some(
          (b) =>
            b.geometry_role === "SUPPORT_CONTOUR" &&
            b.component_template_code === "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        ),
        noSupportError: !afterConfirm.supportError,
        reloadKeepsSupport:
          roles.some((r) => r.key === "pseudo:fill-c5c6c6" && r.conf === "support_panel") ||
          bindings.some((b) => b.geometry_role === "SUPPORT_CONTOUR"),
      },
    };
    fs.writeFileSync(path.join(OUT, "acm_client_case.json"), JSON.stringify(caseAcm, null, 2));
    summary.cases.push(caseAcm);
    await page.close();
  }

  // --- Simple letters ---
  {
    const file = path.join(FIX, "litere-vol-1-layer.svg");
    const ws = await createWs(`repair-letters-${Date.now()}`);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForTimeout(1500);
    await clientUpload(page, file);
    await page.screenshot({ path: path.join(SHOTS, "04_simple_letters.png"), fullPage: true });
    const probe = await probeRoles(page);
    const caseLetters = {
      id: "simple_letters",
      workspace_id: ws.id,
      probe,
      pass: {
        hasFace: probe.roles.some((r) => r.value === "face"),
        noSupportForced: !probe.roles.some((r) => r.value === "support_panel"),
      },
    };
    fs.writeFileSync(path.join(OUT, "simple_letters_case.json"), JSON.stringify(caseLetters, null, 2));
    summary.cases.push(caseLetters);
    await page.close();
  }

  // --- Server upload hydration ---
  {
    const file = path.join(FIX, "litere-cu-fundal-acm-segmentat.svg");
    const ws = await createWs(`repair-server-${Date.now()}`);
    const up = await uploadServer(ws.id, file);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(`${UI}/intake-v6/${ws.id}/operator`, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForTimeout(8000);
    await page.screenshot({ path: path.join(SHOTS, "05_server_upload_hydrated.png"), fullPage: true });
    const probe = await probeRoles(page);
    const api = await getWs(ws.id);
    const caseServer = {
      id: "server_upload",
      workspace_id: ws.id,
      uploadStatus: up.status,
      hasSourceText: typeof api.payload?.svg_source_text === "string",
      probe,
      pass: {
        sourceTextStored: typeof api.payload?.svg_source_text === "string" && api.payload.svg_source_text.length > 0,
        page1NotEmpty: !probe.empty && probe.roles.length > 0,
      },
    };
    fs.writeFileSync(path.join(OUT, "server_upload_case.json"), JSON.stringify(caseServer, null, 2));
    summary.cases.push(caseServer);
    await page.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, "repair_live_summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
