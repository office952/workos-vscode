/**
 * Live screenshots for Intake V6 vocabulary / mounting noise cleanup.
 * Uses FE :3001 (proxy) + BE :8003.
 */
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const UI = process.env.PW_BASE_URL || "http://127.0.0.1:3001";
const BACKEND = process.env.PW_BACKEND_URL || "http://127.0.0.1:8003";
const SVG = path.join(
  process.env.USERPROFILE || "",
  "Desktop",
  "fisiere-teste-svg",
  "litere-cu-fundal-acm-segmentat.svg",
);
const OUT = path.join(
  ROOT,
  "docs",
  "qa",
  "intake-v6-vocabulary-residual-ui-cleanup-2026-07-19",
  "screenshots",
);
const INDEX = path.join(
  ROOT,
  "docs",
  "qa",
  "intake-v6-vocabulary-residual-ui-cleanup-2026-07-19",
  "screenshots_index.md",
);

fs.mkdirSync(OUT, { recursive: true });

const notes = [];

async function createWorkspace() {
  const res = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: `vocab-cleanup-${Date.now()}`,
      analyzer_mode: "analyzer_first",
    }),
  });
  if (!res.ok) throw new Error(`create workspace ${res.status}`);
  return res.json();
}

async function shot(page, name, meta) {
  const file = path.join(OUT, name);
  await page.screenshot({ path: file, fullPage: true });
  notes.push({ file: name, ...meta, path: file.replace(/\\/g, "/") });
  console.log("shot", name);
}

async function gotoReview(page, id) {
  await page.goto(`${UI}/intake-v6/${id}/operator`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
}

async function main() {
  if (!fs.existsSync(SVG)) throw new Error(`SVG missing: ${SVG}`);
  const ws = await createWorkspace();
  console.log("workspace", ws.id, ws.workspace_code);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  await gotoReview(page, ws.id);

  // Page 1 — upload SVG if file input present
  const fileInput = page.locator('input[type="file"]').first();
  if (await fileInput.count()) {
    await fileInput.setInputFiles(SVG);
    await page.waitForTimeout(4000);
  }

  // Try advance to Configurare / review
  for (const label of ["Continuă", "Configurare", "Review"]) {
    const btn = page.getByRole("button", { name: new RegExp(label, "i") }).first();
    if (await btn.isVisible().catch(() => false)) {
      if (await btn.isEnabled().catch(() => false)) {
        await btn.click().catch(() => {});
        await page.waitForTimeout(2000);
      }
    }
  }

  // Tabs
  const tabIlum = page.getByTestId("intake-v6-review-tab-iluminare").or(
    page.getByRole("button", { name: /Iluminare/i }),
  );
  const tabMontaj = page.getByTestId("intake-v6-review-tab-montaj").or(
    page.getByRole("button", { name: /^Montaj$/i }),
  );

  await shot(page, "01_page2_tab_labels.png", {
    url: page.url(),
    workspace: ws.workspace_code,
    svg: path.basename(SVG),
    tab: "review",
    expected: "Finisaje / Iluminare și surse / Montaj",
  });

  if (await tabIlum.first().isVisible().catch(() => false)) {
    await tabIlum.first().click();
    await page.waitForTimeout(800);
  }
  await shot(page, "02_iluminare_si_surse.png", {
    url: page.url(),
    workspace: ws.workspace_code,
    tab: "iluminare",
    expected: "Iluminare și surse / Alimentare LED",
  });

  if (await tabMontaj.first().isVisible().catch(() => false)) {
    await tabMontaj.first().click();
    await page.waitForTimeout(1000);
  }
  await shot(page, "03_fundal_si_carcasa.png", {
    url: page.url(),
    workspace: ws.workspace_code,
    tab: "montaj",
    section: "fundal",
    expected: "Fundal și carcasă cluster visible",
  });

  const commercialToggle = page.getByTestId("intake-v6-montaj-commercial-cluster-toggle");
  if (await commercialToggle.count()) {
    const expanded = await page
      .getByTestId("intake-v6-montaj-commercial-cluster")
      .getAttribute("data-expanded");
    if (expanded === "true") {
      await commercialToggle.click();
      await page.waitForTimeout(400);
    }
    await shot(page, "04_montaj_comercial_collapsed.png", {
      url: page.url(),
      workspace: ws.workspace_code,
      section: "montaj-comercial",
      expected: "collapsed accordion",
    });
    await commercialToggle.click();
    await page.waitForTimeout(400);
    await shot(page, "05_montaj_comercial_expanded.png", {
      url: page.url(),
      workspace: ws.workspace_code,
      section: "montaj-comercial",
      expected: "site section inside commercial",
    });
  }

  const advancedToggle = page.getByTestId("intake-v6-montaj-advanced-cluster-toggle");
  if (await advancedToggle.count()) {
    await shot(page, "06_avansat_collapsed.png", {
      url: page.url(),
      workspace: ws.workspace_code,
      section: "avansat",
      expected: "Avansat collapsed",
    });
    await advancedToggle.click();
    await page.waitForTimeout(400);
    await shot(page, "07_avansat_diagnostics_raw.png", {
      url: page.url(),
      workspace: ws.workspace_code,
      section: "avansat",
      expected: "ownership notes / technical raw allowed",
    });
  }

  // Owner decision / ACP if present
  const readiness = page.getByTestId("intake-v6-acp-module-readiness").first();
  if (await readiness.count()) {
    await readiness.scrollIntoViewIfNeeded().catch(() => {});
    await shot(page, "08_owner_decision_primary.png", {
      url: page.url(),
      workspace: ws.workspace_code,
      section: "acp-modules",
      expected: "Romanian owner decision, no OWNER_GATE text",
    });
  } else {
    await shot(page, "08_owner_decision_primary.png", {
      url: page.url(),
      workspace: ws.workspace_code,
      section: "acp-modules",
      expected: "ACP modules may be absent on this fixture path",
      note: "fallback full montaj page",
    });
  }

  const banner = page.getByTestId("intake-v6-review-operator-blocker-banner").first();
  if (await banner.count()) {
    await banner.scrollIntoViewIfNeeded().catch(() => {});
  }
  await shot(page, "09_sticky_blocker_summary.png", {
    url: page.url(),
    workspace: ws.workspace_code,
    section: "blocker-banner",
    expected: "sticky actionable blockers",
  });

  // Segmented / electrical if present after confirm attempts
  const segConfirm = page.getByTestId("intake-v6-segmented-confirm").or(
    page.getByRole("button", { name: /Confirmă ansamblu|Confirmă segment/i }),
  );
  if (await segConfirm.first().isVisible().catch(() => false)) {
    await segConfirm.first().click().catch(() => {});
    await page.waitForTimeout(2000);
  }
  await shot(page, "10_segmented_confirmed_or_proposal.png", {
    url: page.url(),
    workspace: ws.workspace_code,
    section: "segmented",
    expected: "proposal or confirmed RO labels",
  });

  const elec = page.getByTestId("intake-v6-segmented-electrical-panel").first();
  if (await elec.count()) {
    await elec.scrollIntoViewIfNeeded().catch(() => {});
  }
  await shot(page, "11_electrical_panel.png", {
    url: page.url(),
    workspace: ws.workspace_code,
    section: "electrical",
    expected: "RO supply labels",
  });

  await shot(page, "12_final_confirmation_footer.png", {
    url: page.url(),
    workspace: ws.workspace_code,
    section: "footer",
    expected: "Continuă / Confirmare state",
  });

  await shot(page, "13_full_montaj_page.png", {
    url: page.url(),
    workspace: ws.workspace_code,
    tab: "montaj",
    expected: "full Montaj composition",
  });

  // Scan primary visible text for OWNER_GATE
  const bodyText = await page.locator("body").innerText();
  const ownerGateInPrimary = /OWNER_GATE/.test(bodyText);
  // Advanced may still have ownership notes without OWNER_GATE_REQUIRED string
  const indexLines = [
    "# Screenshots — vocabulary residual UI cleanup",
    "",
    `- UI: ${UI}`,
    `- BE: ${BACKEND}`,
    `- Workspace: ${ws.workspace_code} (${ws.id})`,
    `- SVG: ${path.basename(SVG)}`,
    `- OWNER_GATE visible in body text (incl. advanced): ${ownerGateInPrimary}`,
    "",
    "| # | File | Notes |",
    "|---|------|-------|",
    ...notes.map(
      (n, i) =>
        `| ${i + 1} | ${n.file} | ${n.expected || ""} ${n.note || ""} |`,
    ),
    "",
    "Figma frame screenshot: `14_figma_montaj_runtime_sync.png`",
    "File key `0CDPIuqoaZ1OQgNnvNyl1F` · frame `Intake V6 — Page 2 Montaj (runtime sync 2026-07-19)` · node `74:3`",
  ];
  fs.writeFileSync(INDEX, indexLines.join("\n"), "utf8");
  fs.writeFileSync(
    path.join(OUT, "..", "capture_meta.json"),
    JSON.stringify({ workspace: ws, notes, ownerGateInPrimary, ui: UI, backend: BACKEND }, null, 2),
    "utf8",
  );

  await browser.close();
  console.log("done", { ownerGateInPrimary, shots: notes.length });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
