import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/qa/segmented-electrical-2026-07-19");
const shots = path.join(OUT, "screenshots");
const runtime = path.join(OUT, "runtime");
fs.mkdirSync(shots, { recursive: true });
fs.mkdirSync(runtime, { recursive: true });

const BACKEND = process.env.PW_BACKEND_URL || "http://127.0.0.1:8002";
const UI = process.env.PW_BASE_URL || "http://127.0.0.1:3000";
const workspaceId = process.argv[2];
if (!workspaceId) {
  console.error("usage: node _capture_segmented_electrical_ui.mjs <workspaceId>");
  process.exit(1);
}

async function getWs() {
  const r = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${workspaceId}`);
  return r.json();
}

async function putFinish(finish) {
  const r = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${workspaceId}/finish-setup`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(finish),
  });
  const text = await r.text();
  let body = null;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  return { status: r.status, body };
}

async function goMontaj(page) {
  await page.goto(`${UI}/intake-v6/${workspaceId}/operator`, {
    waitUntil: "domcontentloaded",
    timeout: 120000,
  });
  await page.getByText("Se verifică sesiunea").waitFor({ state: "detached", timeout: 60000 }).catch(() => undefined);
  await page.waitForTimeout(1000);
  // Prefer direct review progress step, else footer continue
  const review = page.getByTestId("intake-v6-progress-step-review");
  if (await review.isVisible().catch(() => false)) {
    await review.click();
  } else {
    await page.getByTestId("intake-v6-footer-next").click().catch(() => undefined);
  }
  await page.waitForTimeout(1200);
  // Montaj tab — several possible labels/testids
  const candidates = [
    page.getByTestId("intake-v6-review-tab-montaj"),
    page.locator('[data-testid*="montaj"]'),
    page.getByRole("tab", { name: /Montaj/i }),
    page.getByRole("button", { name: /^Montaj$/i }),
    page.getByText(/^Montaj$/i),
  ];
  for (const loc of candidates) {
    const el = loc.first();
    if (await el.isVisible().catch(() => false)) {
      await el.click().catch(() => undefined);
      break;
    }
  }
  await page.waitForTimeout(1000);
  // Ensure electrical / segmented panels in view
  const elec = page.getByTestId("intake-v6-segmented-electrical-panel");
  const seg = page.getByTestId("intake-v6-segmented-background-panel");
  if (await elec.isVisible().catch(() => false)) {
    await elec.scrollIntoViewIfNeeded().catch(() => undefined);
  } else if (await seg.isVisible().catch(() => false)) {
    await seg.scrollIntoViewIfNeeded().catch(() => undefined);
  }
  await page.waitForTimeout(500);
}

async function shot(page, name) {
  const p = path.join(shots, `${name}.png`);
  await page.screenshot({ path: p, fullPage: true });
  return p;
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
const ws = await getWs();
let finish = { ...(ws.payload?.finish_setup || {}) };
const seg = { ...(finish.segmented_background || {}) };
if (String(seg.status || "").toUpperCase() !== "CONFIRMED") {
  console.error("workspace segmented not CONFIRMED", seg.status);
  process.exit(2);
}

// 01 before electrical
await goMontaj(page);
const p1 = await shot(page, "01_confirmed_assembly_before_electrical");

// Draft unresolved
seg.electrical_connection_management = {
  schema: "acm_segmented_electrical_connection_v1",
  status: "DRAFT",
  operator_confirmed: false,
  panels: (seg.panels || []).map((p) => ({
    panel_id: p.panel_id,
    supply_mode: "UNCONFIRMED",
  })),
  inter_panel_connections: [],
};
finish = { ...finish, segmented_background: seg };
let put = await putFinish(finish);
fs.writeFileSync(path.join(runtime, "put_unresolved.json"), JSON.stringify(put, null, 2));
await page.reload({ waitUntil: "domcontentloaded" });
await goMontaj(page);
const p2 = await shot(page, "02_unresolved_service_points");

// Case A direct positions via UI if panel visible, else PUT
const panelVisible = await page.getByTestId("intake-v6-segmented-electrical-panel").isVisible().catch(() => false);
fs.writeFileSync(
  path.join(runtime, "ui_panel_visible.json"),
  JSON.stringify({ panelVisible, workspaceId }, null, 2),
);

if (panelVisible) {
  await page.getByTestId("intake-v6-elec-supply-panel_1").selectOption("DIRECT_220V");
  await page.waitForTimeout(500);
  await page.getByTestId("intake-v6-elec-position-panel_1").selectOption("TOP_RIGHT");
  await page.waitForTimeout(400);
  await page.getByTestId("intake-v6-elec-supply-panel_2").selectOption("DIRECT_220V");
  await page.waitForTimeout(400);
  await page.getByTestId("intake-v6-elec-position-panel_2").selectOption("TOP_LEFT");
  await page.waitForTimeout(800);
  const p3 = await shot(page, "03_direct_top_right_top_left");
  await page.getByTestId("intake-v6-elec-supply-panel_2").selectOption("SHARED_FROM_PANEL");
  await page.waitForTimeout(500);
  await page.getByTestId("intake-v6-elec-shared-panel_2").selectOption("panel_1");
  await page.waitForTimeout(800);
  const p4 = await shot(page, "04_shared_from_panel_1");
  // confirm electrical
  const confirm = page.getByTestId("intake-v6-segmented-electrical-confirm");
  if (await confirm.isEnabled()) {
    await confirm.click();
    await page.waitForTimeout(2000);
  }
  const p5 = await shot(page, "05_confirmed_after_save");
  await page.reload({ waitUntil: "domcontentloaded" });
  await goMontaj(page);
  const p6 = await shot(page, "06_confirmed_after_reload");
  console.log(JSON.stringify({ workspaceId, panelVisible, shots: [p1, p2, p3, p4, p5, p6] }, null, 2));
} else {
  // API fallback for screenshots after PUT confirmed shared
  const panels = seg.panels || [];
  seg.electrical_connection_management = {
    schema: "acm_segmented_electrical_connection_v1",
    status: "CONFIRMED",
    operator_confirmed: true,
    panels: [
      {
        panel_id: panels[0].panel_id,
        supply_mode: "DIRECT_220V",
        service_point_position: "TOP_RIGHT",
        routing_direction_note_ro: "spre coltul dreapta sus",
        workshop_prep: { cables_routed_toward_service: true, reserve_required: true },
        installation: { connect_to_client_220v: true },
      },
      {
        panel_id: panels[1].panel_id,
        supply_mode: "SHARED_FROM_PANEL",
        shared_from_panel_id: panels[0].panel_id,
        installation: { finalize_after_alignment: true },
      },
    ],
    inter_panel_connections: [
      {
        connection_id: "ec_live",
        source_panel_id: panels[0].panel_id,
        destination_panel_id: panels[1].panel_id,
        alignment_dependent: true,
        prepared_in_workshop: true,
        completed_on_site: true,
        reserve_required: true,
        length_is_estimate: true,
      },
    ],
  };
  put = await putFinish({ ...finish, segmented_background: seg });
  fs.writeFileSync(path.join(runtime, "put_confirmed_shared.json"), JSON.stringify(put, null, 2));
  await page.reload({ waitUntil: "domcontentloaded" });
  await goMontaj(page);
  const p3 = await shot(page, "03_direct_or_shared_api_fallback");
  console.log(JSON.stringify({ workspaceId, panelVisible, putStatus: put.status, shots: [p1, p2, p3] }, null, 2));
}

const after = await getWs();
fs.writeFileSync(path.join(runtime, "workspace_after.json"), JSON.stringify(after.payload?.finish_setup?.segmented_background, null, 2));
const pd = await fetch(
  `${BACKEND}/api/v1/product-system/product-definition/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=${workspaceId}`,
).then((r) => r.json());
fs.writeFileSync(path.join(runtime, "pd_after.json"), JSON.stringify(pd?.canonical_values?.segmented_background || pd, null, 2));

await browser.close();
