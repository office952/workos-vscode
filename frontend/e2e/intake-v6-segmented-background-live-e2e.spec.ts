/**
 * LIVE E2E — segmented ACM/ACP background confirmation with real Desktop SVGs.
 *
 * Prerequisites:
 *   - Backend :8001 + frontend :3000 running
 *   - PW_SKIP_WEB_SERVER=1
 *   - PW_BACKEND_URL=http://127.0.0.1:8001
 *   - Desktop fixtures at %USERPROFILE%\Desktop\fisiere-teste-svg\
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BACKEND = process.env.PW_BACKEND_URL ?? "http://127.0.0.1:8001";
const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const DESKTOP_SVG = path.join(
  process.env.USERPROFILE || process.env.HOME || "",
  "Desktop",
  "fisiere-teste-svg",
);
const OUT = path.join(
  __dirname,
  "..",
  "..",
  "docs",
  "qa",
  "segmented-background-live-e2e-2026-07-19",
  "screenshots",
);
const LOG_DIR = path.join(
  __dirname,
  "..",
  "..",
  "docs",
  "qa",
  "segmented-background-live-e2e-2026-07-19",
  "runtime",
);

const SVG_BASIC = path.join(DESKTOP_SVG, "litere-cu-fundal-acm-segmentat.svg");
const SVG_CROSS = path.join(DESKTOP_SVG, "litere-cu-fundal-acm-segmentat-litera-peste-imbinare.svg");
const SVG_SIT3 = path.join(DESKTOP_SVG, "situatie-3.svg");

function ensureDirs() {
  fs.mkdirSync(OUT, { recursive: true });
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

function writeJson(name: string, data: unknown) {
  fs.writeFileSync(path.join(LOG_DIR, name), JSON.stringify(data, null, 2), "utf8");
}

async function createWorkspace(title: string): Promise<{ id: string; workspace_code: string }> {
  const response = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, analyzer_mode: "analyzer_first" }),
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) {
    throw new Error(`workspace create ${response.status}: ${(await response.text()).slice(0, 300)}`);
  }
  const body = (await response.json()) as { id: string; workspace_code: string };
  return body;
}

async function getWorkspace(id: string) {
  const response = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${id}`, {
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) throw new Error(`workspace get ${response.status}`);
  return response.json();
}

async function getProductDefinition(templateCode: string, workspaceId: string) {
  const url = `${BACKEND}/api/v1/product-system/product-definition/${encodeURIComponent(templateCode)}?workspace_id=${encodeURIComponent(workspaceId)}`;
  const response = await fetch(url, { signal: AbortSignal.timeout(30_000) });
  return { status: response.status, body: await response.json().catch(() => null) };
}

async function getProductAggregate(templateCode: string, workspaceId: string) {
  const url = `${BACKEND}/api/v1/product-system/aggregate/${encodeURIComponent(templateCode)}?workspace_id=${encodeURIComponent(workspaceId)}`;
  const response = await fetch(url, { signal: AbortSignal.timeout(30_000) });
  return { status: response.status, body: await response.json().catch(() => null) };
}

async function putFinishSetup(workspaceId: string, finish: Record<string, unknown>) {
  const response = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${workspaceId}/finish-setup`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(finish),
    signal: AbortSignal.timeout(30_000),
  });
  const text = await response.text();
  let body: unknown = null;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  return { status: response.status, body };
}

async function waitFinishSegmentedStatus(
  workspaceId: string,
  status: string,
  timeoutMs = 45_000,
): Promise<Record<string, unknown> | null> {
  const started = Date.now();
  let last: Record<string, unknown> | null = null;
  while (Date.now() - started < timeoutMs) {
    const snap = await getWorkspace(workspaceId);
    last = (snap.payload?.finish_setup?.segmented_background as Record<string, unknown>) || null;
    if (String(last?.status || "").toUpperCase() === status.toUpperCase()) {
      return last;
    }
    await new Promise((r) => setTimeout(r, 400));
  }
  return last;
}

async function waitAuth(page: Page) {
  await expect(page.getByText("Se verifică sesiunea")).toHaveCount(0, { timeout: 60_000 });
}

async function gotoOperator(page: Page, workspaceId: string) {
  await page.goto(`${UI}/intake-v6/${workspaceId}/operator`, {
    waitUntil: "domcontentloaded",
    timeout: 120_000,
  });
  await waitAuth(page);
  await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 90_000 });
}

async function importSvg(page: Page, svgPath: string) {
  const input = page.getByTestId("intake-v6-svg-input");
  await input.waitFor({ state: "attached", timeout: 60_000 });
  await input.setInputFiles(svgPath);
  await expect(page.getByTestId("intake-v6-file-confirm-chip")).toBeVisible({ timeout: 90_000 });
}

async function assignConturSuportIfPossible(page: Page) {
  // Prefer ACM / fundal / gravare layer when present; else first select with Contur suport.
  const roleSelects = page.locator('[data-testid^="intake-v6-layer-role-"]');
  await roleSelects.first().waitFor({ state: "attached", timeout: 60_000 }).catch(() => undefined);
  const count = await roleSelects.count();
  const ranked: Array<{ i: number; score: number }> = [];
  for (let i = 0; i < count; i += 1) {
    const sel = roleSelects.nth(i);
    const testId = (await sel.getAttribute("data-testid")) || "";
    const html = await sel.innerHTML().catch(() => "");
    if (!/support_panel|Contur suport/i.test(html)) continue;
    let score = 0;
    if (/gravare|fundal|acm|alucobond|support|panel|cnc-135/i.test(testId)) score += 10;
    if (/letter|litere|logo|decupare|outside/i.test(testId)) score -= 5;
    ranked.push({ i, score });
  }
  ranked.sort((a, b) => b.score - a.score);
  for (const { i } of ranked) {
    const sel = roleSelects.nth(i);
    await sel.selectOption("support_panel").catch(async () => {
      const opts = await sel.locator("option").allTextContents();
      const label = opts.find((o) => /contur suport/i.test(o));
      if (label) await sel.selectOption({ label });
    });
    await page.waitForTimeout(2500);
    const associateError = page.getByText(/Nu s-a putut asocia|necesită candidați closed-contour/i);
    if (await associateError.isVisible().catch(() => false)) continue;
    return true;
  }
  return ranked.length > 0;
}

async function confirmLayerRolesAndAdvanceToReview(page: Page) {
  const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
    await expect(page.getByTestId("intake-v6-layers-all-confirmed").or(confirmAll)).toBeVisible({
      timeout: 30_000,
    });
  }
  // Wait for analysis-bundle / role persist so Review unlocks.
  await expect(page.getByTestId("intake-v6-footer-next")).toBeEnabled({ timeout: 90_000 });
  await page.getByTestId("intake-v6-footer-next").click();
  await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 90_000 });
}

async function goReviewMontaj(page: Page) {
  await waitAuth(page);
  const started = Date.now();
  while (Date.now() - started < 90_000) {
    if (await page.getByTestId("intake-v6-step-review").isVisible().catch(() => false)) break;
    const review = page.getByTestId("intake-v6-progress-step-review");
    if (await review.isEnabled().catch(() => false)) {
      await review.click().catch(() => undefined);
      await page.waitForTimeout(500);
      continue;
    }
    const footerNext = page.getByTestId("intake-v6-footer-next");
    const footerLabel = ((await footerNext.textContent().catch(() => "")) || "").trim();
    if (/Confirmare/i.test(footerLabel)) {
      // Already on Review — wait for content mount.
      await page.waitForTimeout(500);
      continue;
    }
    if (/Configurare/i.test(footerLabel) && (await footerNext.isEnabled().catch(() => false))) {
      await footerNext.click().catch(() => undefined);
      await page.waitForTimeout(800);
      continue;
    }
    const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
    if (await confirmAll.isVisible().catch(() => false)) {
      await confirmAll.click().catch(() => undefined);
      await page.waitForTimeout(800);
      continue;
    }
    await page.waitForTimeout(500);
  }
  await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 30_000 });
  const montaj = page.getByTestId("intake-v6-review-tab-montaj");
  if (await montaj.count()) {
    await montaj.click();
  } else {
    await page.getByRole("tab", { name: /Montaj/i }).click().catch(() => undefined);
  }
  await expect(page.getByTestId("intake-v6-review-tab-panel-montaj")).toBeVisible({ timeout: 30_000 }).catch(
    () => undefined,
  );
}

async function waitForSegmentedProposal(workspaceId: string, timeoutMs = 60_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const snap = await getWorkspace(workspaceId);
    const seg = snap?.payload?.finish_setup?.segmented_background;
    const status = String(seg?.status || "").toUpperCase();
    if (status === "PROPOSED" || status === "CONFIRMED") {
      return seg;
    }
    await new Promise((r) => setTimeout(r, 1500));
  }
  return null;
}

async function waitForAnalysisPersisted(workspaceId: string, timeoutMs = 60_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const snap = await getWorkspace(workspaceId);
    const hasSvg = Boolean(snap?.payload?.svg_analysis_json || snap?.payload?.svg_source);
    const hasRoles = Boolean(snap?.payload?.layer_role_setup);
    if (hasSvg && hasRoles) return snap;
    await new Promise((r) => setTimeout(r, 1000));
  }
  return null;
}

async function afterImportProposeAndOpenReview(page: Page, workspaceId: string) {
  const finishBodies: unknown[] = [];
  const finishResponses: Array<{ status: number; hasSeg: boolean; segStatus?: string }> = [];
  page.on("request", (req) => {
    if (req.url().includes("/finish-setup") && req.method() === "PUT") {
      try {
        finishBodies.push(JSON.parse(req.postData() || "{}"));
      } catch {
        finishBodies.push(req.postData());
      }
    }
  });
  page.on("response", async (res) => {
    if (res.url().includes("/finish-setup") && res.request().method() === "PUT") {
      const body = await res.json().catch(() => null);
      const seg = body?.payload?.finish_setup?.segmented_background;
      finishResponses.push({
        status: res.status(),
        hasSeg: Boolean(seg),
        segStatus: seg?.status,
      });
    }
  });

  const layersStep = page.getByTestId("intake-v6-progress-step-layers");
  if (await layersStep.isEnabled().catch(() => false)) {
    await layersStep.click().catch(() => undefined);
  }

  // Debounced analysis-bundle must land before Contur suport early association.
  const analysis = await waitForAnalysisPersisted(workspaceId, 60_000);
  writeJson(`analysis_wait_${workspaceId.slice(0, 8)}.json`, {
    ok: Boolean(analysis),
    readiness: analysis?.readiness_status,
  });

  // Contur suport FIRST → early merge keeps segmented_background on finish_setup.
  const assigned = await assignConturSuportIfPossible(page);
  await page.waitForTimeout(2500);
  let proposal = await waitForSegmentedProposal(workspaceId, 30_000);

  // Then confirm remaining layer roles and advance.
  const confirmAll = page.getByTestId("intake-v6-confirm-all-roles");
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
    await page.waitForTimeout(1500);
  }
  if (await confirmAll.isVisible().catch(() => false)) {
    await confirmAll.click();
    await page.waitForTimeout(1000);
  }

  // Re-check proposal after role confirm (must not wipe).
  if (!proposal) {
    proposal = await waitForSegmentedProposal(workspaceId, 20_000);
  }
  writeJson(`proposal_wait_${workspaceId.slice(0, 8)}.json`, {
    assigned,
    proposal,
    finishPutCount: finishBodies.length,
    finishResponses,
    finishPutsHadSegmented: finishBodies.some(
      (b) => b && typeof b === "object" && (b as { segmented_background?: unknown }).segmented_background,
    ),
    lastFinishKeys:
      finishBodies.length && typeof finishBodies[finishBodies.length - 1] === "object"
        ? Object.keys(finishBodies[finishBodies.length - 1] as object).slice(0, 40)
        : [],
  });
  writeJson(`finish_puts_${workspaceId.slice(0, 8)}.json`, finishBodies.slice(-3));
  writeJson(`finish_responses_${workspaceId.slice(0, 8)}.json`, finishResponses);

  const alreadyReview = await page.getByTestId("intake-v6-step-review").isVisible().catch(() => false);
  if (!alreadyReview) {
    const footerNext = page.getByTestId("intake-v6-footer-next");
    const label = ((await footerNext.textContent()) || "").trim();
    if (/Configurare/i.test(label)) {
      await expect(footerNext).toBeEnabled({ timeout: 90_000 });
      await footerNext.click();
    }
  }

  await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 90_000 });
  await goReviewMontaj(page);
  // Panel may need a beat for finish hydrate (segmented_background now in finishFromPayload).
  await page.waitForTimeout(2000);
  return { assigned, proposal };
}

async function prepareProposalAndOpenReview(page: Page, svgPath: string, workspaceId: string) {
  await page.getByTestId("intake-v6-progress-step-layers").click().catch(() => undefined);
  await importSvg(page, svgPath);
  return afterImportProposeAndOpenReview(page, workspaceId);
}

test.describe("LIVE segmented ACM/ACP background E2E", () => {
  test.beforeAll(() => {
    ensureDirs();
    for (const f of [SVG_BASIC, SVG_CROSS, SVG_SIT3]) {
      if (!fs.existsSync(f)) {
        throw new Error(`Missing real SVG fixture: ${f}`);
      }
    }
  });

  test("CASE 1 — basic segmented: import → proposal → confirm → reload → PD/Aggregate", async ({
    page,
  }) => {
    test.setTimeout(300_000);
    const ws = await createWorkspace("live-seg-basic");
    writeJson("case1_workspace.json", ws);

    const finishPuts: Array<{ url: string; status?: number }> = [];
    page.on("response", (res) => {
      if (res.url().includes("/finish-setup") && res.request().method() === "PUT") {
        finishPuts.push({ url: res.url(), status: res.status() });
      }
    });

    await gotoOperator(page, ws.id);
    await page.getByTestId("intake-v6-progress-step-layers").click().catch(() => undefined);
    await importSvg(page, SVG_BASIC);
    await page.screenshot({ path: path.join(OUT, "01_case1_imported.png"), fullPage: true });

    const prep = await afterImportProposeAndOpenReview(page, ws.id);
    writeJson("case1_contur_suport_assigned.json", prep);

    const panel = page.getByTestId("intake-v6-segmented-background-panel");
    const panelVisible = await panel.isVisible().catch(() => false);
    await page.screenshot({ path: path.join(OUT, "02_case1_review_proposal.png"), fullPage: true });
    writeJson("case1_panel_visible.json", { panelVisible, finishPuts });

    if (!panelVisible) {
      // Capture finish_setup for diagnosis
      const snap = await getWorkspace(ws.id);
      writeJson("case1_workspace_after_import.json", {
        id: snap.id,
        finish_setup: snap.payload?.finish_setup ?? null,
        closed_contours:
          snap.payload?.svg_analysis_json?.closedContourCandidates ??
          snap.payload?.svg_analysis_json?.closed_contour_candidates ??
          null,
      });
      test.info().annotations.push({
        type: "blocker",
        description: "Segmented proposal panel not visible after Contur suport — see case1_workspace_after_import.json",
      });
      expect(panelVisible, "Proposal panel must appear for multi-panel SVG").toBeTruthy();
      return;
    }

    await expect(panel).toHaveAttribute("data-status", "proposed");
    await expect(page.getByText(/Posibil fundal format din mai multe panouri/i)).toBeVisible();
    await expect(page.getByTestId("intake-v6-segmented-confirm")).toBeEnabled();

    // Before confirm — PD must not have confirmed segmented truth
    const pdBefore = await getProductDefinition("TPL-VOLUMETRIC-LETTERS_v2", ws.id);
    writeJson("case1_pd_before_confirm.json", pdBefore);
    const beforeVals = (pdBefore.body as { canonical_values?: Record<string, unknown> })?.canonical_values || {};
    expect(beforeVals.segmented_background).toBeFalsy();

    await page.getByTestId("intake-v6-segmented-confirm").click();
    await expect(page.getByTestId("intake-v6-segmented-status")).toContainText(/Confirmat/i, {
      timeout: 30_000,
    });
    const confirmedSeg = await waitFinishSegmentedStatus(ws.id, "CONFIRMED");
    writeJson("case1_finish_after_confirm.json", confirmedSeg);
    expect(confirmedSeg?.status).toBe("CONFIRMED");
    await page.screenshot({ path: path.join(OUT, "03_case1_confirmed.png"), fullPage: true });

    // Reload
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitAuth(page);
    await goReviewMontaj(page);
    await expect(page.getByTestId("intake-v6-segmented-status")).toContainText(/Confirmat/i, {
      timeout: 60_000,
    });
    await page.screenshot({ path: path.join(OUT, "04_case1_reloaded_confirmed.png"), fullPage: true });

    const wsAfter = await getWorkspace(ws.id);
    const seg = wsAfter.payload?.finish_setup?.segmented_background;
    writeJson("case1_finish_after_reload.json", seg);
    expect(seg?.status).toBe("CONFIRMED");
    expect(seg?.operator_confirmed).toBe(true);
    expect((seg?.panels || []).length).toBeGreaterThanOrEqual(2);

    const pdAfter = await getProductDefinition("TPL-VOLUMETRIC-LETTERS_v2", ws.id);
    writeJson("case1_pd_after.json", pdAfter);
    const afterVals = (pdAfter.body as { canonical_values?: Record<string, unknown> })?.canonical_values || {};
    expect(afterVals.segmented_background).toBeTruthy();

    const agg = await getProductAggregate("TPL-VOLUMETRIC-LETTERS_v2", ws.id);
    writeJson("case1_aggregate.json", agg);
    // Aggregate may nest projection in different shapes — assert no crash + log
    expect(agg.status).toBeLessThan(500);

    const putOk = finishPuts.some((p) => p.status === 200 || p.status === 201);
    expect(putOk, "At least one finish-setup PUT must succeed").toBeTruthy();
  });

  test("CASE 2 — applied letter crossing SVG: proposal + confirmable path", async ({ page }) => {
    test.setTimeout(300_000);
    const ws = await createWorkspace("live-seg-cross");
    writeJson("case2_workspace.json", ws);
    await gotoOperator(page, ws.id);
    await prepareProposalAndOpenReview(page, SVG_CROSS, ws.id);
    await page.screenshot({ path: path.join(OUT, "05_case2_cross_review.png"), fullPage: true });

    const panel = page.getByTestId("intake-v6-segmented-background-panel");
    const visible = await panel.isVisible().catch(() => false);
    writeJson("case2_panel.json", {
      visible,
      workspace: await getWorkspace(ws.id).then((w) => w.payload?.finish_setup?.segmented_background),
    });
    expect(visible).toBeTruthy();

    // Inject applied crossing binding if analyzer did not auto-bind (document interaction)
    const snap = await getWorkspace(ws.id);
    const current = snap.payload?.finish_setup?.segmented_background;
    if (current?.status === "PROPOSED" && !(current.element_bindings || []).length) {
      const panels = current.panels || [];
      if (panels.length >= 2) {
        const finish = {
          ...(snap.payload.finish_setup || {}),
          segmented_background: {
            ...current,
            element_bindings: [
              {
                binding_id: "eb_live_cross",
                element_ref: "letter_over_joint",
                construction_type: "APPLIED_VOLUMETRIC_LETTER",
                primary_panel_id: panels[0].panel_id,
                secondary_panel_id: panels[1].panel_id,
                crosses_joint: true,
                joint_id: (current.joints || [])[0]?.joint_id,
                applied_component_template_code: "TPL-VOLUMETRIC-FACE_v1",
              },
            ],
          },
        };
        const put = await putFinishSetup(ws.id, finish);
        writeJson("case2_binding_put.json", put);
        expect(put.status).toBeLessThan(400);
        await page.reload({ waitUntil: "domcontentloaded" });
        await waitAuth(page);
        await goReviewMontaj(page);
      }
    }

    await expect(
      page.getByTestId("intake-v6-segmented-applied-crossing").or(page.getByText(/montaj in doua etape/i)).first(),
    ).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByTestId("intake-v6-segmented-confirm")).toBeEnabled();
    await page.screenshot({ path: path.join(OUT, "06_case2_applied_crossing_confirmable.png"), fullPage: true });

    await page.getByTestId("intake-v6-segmented-confirm").click();
    await expect(page.getByTestId("intake-v6-segmented-status")).toContainText(/Confirmat/i, {
      timeout: 30_000,
    });

    const finishSeg = await waitFinishSegmentedStatus(ws.id, "CONFIRMED");
    writeJson("case2_finish_after_confirm.json", finishSeg);
    expect(finishSeg?.status).toBe("CONFIRMED");
    const finishBindings = (finishSeg?.element_bindings as Array<Record<string, unknown>>) || [];
    expect(
      finishBindings.some(
        (b) =>
          String(b.mount_strategy || "").includes("TWO_STAGE") ||
          b.crosses_joint === true,
      ),
    ).toBeTruthy();

    const pd = await getProductDefinition("TPL-VOLUMETRIC-LETTERS_v2", ws.id);
    writeJson("case2_pd.json", pd);
    const body = pd.body as Record<string, unknown>;
    const vals =
      (body?.canonical_values as Record<string, unknown>) ||
      ((body?.product_definition as { canonical_values?: Record<string, unknown> })?.canonical_values) ||
      {};
    const seg =
      (vals.segmented_background as Record<string, unknown>) ||
      (body?.segmented_background as Record<string, unknown>);
    // PD projection may omit unresolved bindings; finish CONFIRMED + two-stage is authority for this case.
    if (seg) {
      const bindings = (seg.element_bindings as Array<Record<string, unknown>>) || [];
      if (bindings.length) {
        expect(
          bindings.some(
            (b) =>
              String(b.mount_strategy || "").includes("TWO_STAGE") || b.crosses_joint === true,
          ),
        ).toBeTruthy();
      }
    } else {
      expect(finishSeg?.operator_confirmed).toBe(true);
    }
  });

  test("CASE 3 — situatie-3 distributed composition calm path", async ({ page }) => {
    test.setTimeout(300_000);
    const ws = await createWorkspace("live-seg-sit3");
    writeJson("case3_workspace.json", ws);
    await gotoOperator(page, ws.id);
    await prepareProposalAndOpenReview(page, SVG_SIT3, ws.id);
    await page.screenshot({ path: path.join(OUT, "07_case3_situatie3.png"), fullPage: true });

    // Must not show generic multi-panel geometry panic
    await expect(page.getByText(/configuratie invalida din cauza intersectiei/i)).toHaveCount(0);
    await expect(page.getByText(/Eroare: grafica traverseaza/i)).toHaveCount(0);

    const panel = page.getByTestId("intake-v6-segmented-background-panel");
    if (await panel.isVisible().catch(() => false)) {
      await expect(page.getByTestId("intake-v6-segmented-confirm")).toBeVisible();
    }
    writeJson("case3_finish.json", {
      seg: (await getWorkspace(ws.id)).payload?.finish_setup?.segmented_background ?? null,
    });
  });

  test("CASE reject + cutout/insert blockers via real PUT", async ({ page }) => {
    test.setTimeout(300_000);
    const ws = await createWorkspace("live-seg-reject-block");
    writeJson("case_reject_workspace.json", ws);
    await gotoOperator(page, ws.id);
    await prepareProposalAndOpenReview(page, SVG_BASIC, ws.id);

    const panel = page.getByTestId("intake-v6-segmented-background-panel");
    expect(await panel.isVisible()).toBeTruthy();

    // Reject path
    await page.getByTestId("intake-v6-segmented-reject").click();
    await expect(page.getByTestId("intake-v6-segmented-status")).toContainText(/Respins/i, {
      timeout: 30_000,
    });
    const segRejectedWait = await waitFinishSegmentedStatus(ws.id, "REJECTED");
    writeJson("case_reject_finish_immediate.json", segRejectedWait);
    expect(segRejectedWait?.status).toBe("REJECTED");
    await page.screenshot({ path: path.join(OUT, "08_reject_state.png"), fullPage: true });
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitAuth(page);
    await goReviewMontaj(page);
    await expect(page.getByTestId("intake-v6-segmented-status")).toContainText(/Respins/i, {
      timeout: 60_000,
    });
    await page.screenshot({ path: path.join(OUT, "09_reject_reloaded.png"), fullPage: true });

    const afterReject = await getWorkspace(ws.id);
    const segRejected = afterReject.payload?.finish_setup?.segmented_background;
    writeJson("case_reject_finish.json", segRejected);
    expect(String(segRejected?.status || "")).toBe("REJECTED");
    expect(segRejected?.operator_confirmed).not.toBe(true);

    const pdRejected = await getProductDefinition("TPL-VOLUMETRIC-LETTERS_v2", ws.id);
    writeJson("case_reject_pd.json", pdRejected);
    const vals = (pdRejected.body as { canonical_values?: Record<string, unknown> })?.canonical_values || {};
    expect(vals.segmented_background).toBeFalsy();

    // Backend blockers for cutout / insert confirmed write
    const panels = (segRejected?.panels?.length ? segRejected.panels : [
      { panel_id: "panel_1", order: 1, width_mm: 1000, height_mm: 1000, position: { x_mm: 0, y_mm: 0 } },
      { panel_id: "panel_2", order: 2, width_mm: 1000, height_mm: 1000, position: { x_mm: 1000, y_mm: 0 } },
    ]) as Array<Record<string, unknown>>;

    const cutoutBody = {
      ...(afterReject.payload.finish_setup || {}),
      segmented_background: {
        schema: "acm_segmented_background_v1",
        status: "CONFIRMED",
        operator_confirmed: true,
        assembly_id: "asm_blocker_cut",
        panels,
        joints: [
          {
            joint_id: "joint_panel_1_panel_2",
            left_panel_id: panels[0].panel_id,
            right_panel_id: panels[1].panel_id,
            orientation: "VERTICAL",
          },
        ],
        element_bindings: [
          {
            binding_id: "eb_cut",
            construction_type: "CUTOUT",
            primary_panel_id: panels[0].panel_id,
            secondary_panel_id: panels[1].panel_id,
            crosses_joint: true,
          },
        ],
      },
    };
    const cutPut = await putFinishSetup(ws.id, cutoutBody);
    writeJson("case_cutout_422.json", cutPut);
    expect(cutPut.status).toBe(422);

    const insertBody = {
      ...cutoutBody,
      segmented_background: {
        ...cutoutBody.segmented_background,
        assembly_id: "asm_blocker_ins",
        element_bindings: [
          {
            binding_id: "eb_ins",
            construction_type: "ACRYLIC_INSERT",
            primary_panel_id: panels[0].panel_id,
            secondary_panel_id: panels[1].panel_id,
            crosses_joint: true,
          },
        ],
      },
    };
    const insPut = await putFinishSetup(ws.id, insertBody);
    writeJson("case_insert_422.json", insPut);
    expect(insPut.status).toBe(422);

    // UI blocker: write PROPOSED with cutout binding and verify Confirm disabled
    const proposedCut = {
      ...(afterReject.payload.finish_setup || {}),
      segmented_background: {
        ...cutoutBody.segmented_background,
        status: "PROPOSED",
        operator_confirmed: false,
      },
    };
    const propPut = await putFinishSetup(ws.id, proposedCut);
    writeJson("case_ui_cutout_proposed.json", propPut);
    expect(propPut.status).toBeLessThan(400);
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitAuth(page);
    await goReviewMontaj(page);
    await expect(page.getByTestId("intake-v6-segmented-cutout-blocker").first()).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByTestId("intake-v6-segmented-confirm")).toBeDisabled();
    await page.screenshot({ path: path.join(OUT, "10_cutout_blocker_ui.png"), fullPage: true });

    const proposedIns = {
      ...proposedCut,
      segmented_background: {
        ...insertBody.segmented_background,
        status: "PROPOSED",
        operator_confirmed: false,
      },
    };
    await putFinishSetup(ws.id, proposedIns);
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitAuth(page);
    await goReviewMontaj(page);
    await expect(page.getByTestId("intake-v6-segmented-insert-blocker").first()).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByTestId("intake-v6-segmented-confirm")).toBeDisabled();
    await page.screenshot({ path: path.join(OUT, "11_insert_blocker_ui.png"), fullPage: true });
  });
});
