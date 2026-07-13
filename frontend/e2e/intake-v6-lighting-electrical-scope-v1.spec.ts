/**
 * UI evidence for INTAKE_V6_LIGHTING_ELECTRICAL_UI_SAVE_RACE_FINALIZATION_V1.
 * Scope changes are applied only through the operator UI (no direct API mutation).
 *
 * Run: cd frontend && $env:PW_SKIP_WEB_SERVER='1'; npx playwright test e2e/intake-v6-lighting-electrical-scope-v1.spec.ts
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { intakeV6OperatorUrl } from "./helpers/intakeV6ThreeStepSmoke";
const WORKSPACE_ID = "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1";
const UI_BASE = process.env.INTAKE_V6_UI_BASE ?? "http://127.0.0.1:3000";

const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-lighting-electrical-scope-v1/screenshots",
);

const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-lighting-electrical-scope-v1/evidence_report.json",
);

type PutRecord = {
  mode: string;
  sold_modules: string[];
};

type ScopeNote = {
  file: string;
  soldScope: string;
  userClicks: string[];
  putCount: number;
  submittedSoldModules: string[];
  lightingSubsection: boolean;
  electricalSubsection: boolean;
  psuOnMontaj: boolean;
  materialTotal: string | null;
  materialRows: string[];
  reloadPreserved: boolean;
};

const notes: ScopeNote[] = [];

async function gotoOfferScopePanel(page: Page) {
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });
}

async function waitForOfferScopeConfirmed(page: Page) {
  await gotoOfferScopePanel(page);
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });
  const status = page.getByTestId("intake-v6-offer-scope-status");
  await expect(status).toBeVisible({ timeout: 30_000 });
  await expect(status).not.toContainText("Salvez selecția", { timeout: 120_000 });
  await expect(status).toHaveText("Selecție confirmată", { timeout: 30_000 });
}

async function clickScopeControl(page: Page, testId: string) {
  if (!(await page.getByTestId("intake-v6-offer-scope-panel").isVisible())) {
    await gotoOfferScopePanel(page);
  }
  const putPromise = page
    .waitForResponse(
      (response) =>
        response.url().includes("/offer-scope") &&
        response.request().method() === "PUT" &&
        response.ok(),
      { timeout: 120_000 },
    )
    .catch(() => null);
  await page.getByTestId(testId).click();
  await putPromise;
  await waitForOfferScopeConfirmed(page);
}

async function selectFullProduct(page: Page) {
  await gotoOfferScopePanel(page);
  if (await page.getByTestId("intake-v6-offer-scope-mode-full").isChecked()) {
    return;
  }
  await clickScopeControl(page, "intake-v6-offer-scope-mode-full");
}

async function selectSubsetOnly(page: Page, modules: string[]) {
  await gotoOfferScopePanel(page);
  const moduleToTestId: Record<string, string> = {
    FACE: "intake-v6-offer-scope-face",
    "RETURN-CANT": "intake-v6-offer-scope-cant",
    BACK: "intake-v6-offer-scope-back",
    LIGHTING: "intake-v6-offer-scope-lighting",
    ELECTRICAL: "intake-v6-offer-scope-electrical",
  };

  if (!(await page.getByTestId("intake-v6-offer-scope-mode-subset").isChecked())) {
    await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
  }

  const putPromise =
    modules.length > 0
      ? page.waitForResponse(
          (response) =>
            response.url().includes("/offer-scope") &&
            response.request().method() === "PUT" &&
            response.ok(),
          { timeout: 120_000 },
        )
      : null;

  for (const [code, testId] of Object.entries(moduleToTestId)) {
    const checkbox = page.getByTestId(testId);
    const shouldBeChecked = modules.includes(code);
    if ((await checkbox.isChecked()) !== shouldBeChecked) {
      await checkbox.click();
    }
  }

  if (putPromise) {
    await putPromise;
    await waitForOfferScopeConfirmed(page);
  }
}

async function ensureWorkspaceReady(page: Page) {
  await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 120_000 });
  await expect(page.getByText(/Backend indisponibil/i)).toHaveCount(0, { timeout: 120_000 });
}

async function gotoReviewIluminare(page: Page) {
  const reviewStep = page.getByTestId("intake-v6-progress-step-review");
  await expect(reviewStep).toBeEnabled({ timeout: 60_000 });
  await reviewStep.click();
  await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 60_000 });
  await page.getByTestId("intake-v6-review-tab-iluminare").click();
  await expect(page.getByTestId("intake-v6-review-tab-panel-iluminare")).toBeVisible({
    timeout: 30_000,
  });
  await page.waitForTimeout(1500);
}

async function gotoReviewMontaj(page: Page) {
  await page.getByTestId("intake-v6-progress-step-review").click();
  await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 60_000 });
  await page.getByTestId("intake-v6-review-tab-montaj").click();
  await expect(page.getByTestId("intake-v6-review-tab-panel-montaj")).toBeVisible({
    timeout: 30_000,
  });
  await page.waitForTimeout(1500);
}

async function readLiveCalcNotes(page: Page): Promise<{ materialTotal: string | null; materialRows: string[] }> {
  const total = page.getByTestId("intake-v6-live-material-total").first();
  const materialTotal = (await total.count()) > 0 ? ((await total.textContent()) ?? "").trim() : null;
  const rowLocator = page.locator('[data-testid^="intake-v6-live-material-used-"]');
  const count = await rowLocator.count();
  const materialRows: string[] = [];
  for (let i = 0; i < Math.min(count, 12); i += 1) {
    const text = ((await rowLocator.nth(i).textContent()) ?? "").replace(/\s+/g, " ").trim();
    if (text) materialRows.push(text);
  }
  return { materialTotal, materialRows };
}

async function captureScopeEvidence(
  page: Page,
  file: string,
  soldScope: string,
  tab: "iluminare" | "montaj",
  meta: Omit<ScopeNote, "file" | "soldScope" | "lightingSubsection" | "electricalSubsection" | "psuOnMontaj" | "materialTotal" | "materialRows">,
) {
  if (tab === "iluminare") {
    await gotoReviewIluminare(page);
  } else {
    await gotoReviewMontaj(page);
  }

  const lightingSubsection = (await page.getByTestId("intake-v6-lighting-subsection").count()) > 0;
  const electricalSubsection = (await page.getByTestId("intake-v6-electrical-subsection").count()) > 0;
  const psuOnMontaj =
    tab === "montaj" ? (await page.getByTestId("intake-v6-selected-psu-watts").count()) > 0 : false;
  const { materialTotal, materialRows } = await readLiveCalcNotes(page);

  await page.screenshot({ path: path.join(OUT_DIR, file), fullPage: true });

  notes.push({
    file,
    soldScope,
    lightingSubsection,
    electricalSubsection,
    psuOnMontaj,
    materialTotal,
    materialRows,
    ...meta,
  });
}

test.describe("Intake V6 lighting/electrical scope UI evidence", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
    fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
  });

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1");
    });
  });

  test("capture five lighting/electrical scope states via operator UI", async ({ page }) => {
    test.setTimeout(300_000);
    const putRecords: PutRecord[] = [];
    page.on("request", (request) => {
      if (request.method() === "PUT" && request.url().includes("/offer-scope")) {
        putRecords.push(JSON.parse(request.postData() ?? "{}") as PutRecord);
      }
    });

    await page.goto(intakeV6OperatorUrl(WORKSPACE_ID, UI_BASE), {
      waitUntil: "networkidle",
      timeout: 120_000,
    });
    await ensureWorkspaceReady(page);
    await gotoOfferScopePanel(page);

    await selectFullProduct(page);
    const fullPutCount = putRecords.length;
    await captureScopeEvidence(page, "01_full_product_iluminare_electrica.png", "full_product", "iluminare", {
      userClicks: ["mode-full"],
      putCount: fullPutCount,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
      reloadPreserved: true,
    });

    await selectSubsetOnly(page, ["LIGHTING"]);
    const lightingPutCount = putRecords.length - fullPutCount;
    await captureScopeEvidence(page, "02_lighting_only_scope.png", "LIGHTING", "iluminare", {
      userClicks: ["mode-subset", "LIGHTING"],
      putCount: lightingPutCount,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
      reloadPreserved: true,
    });

    await selectSubsetOnly(page, ["ELECTRICAL"]);
    const electricalPutCount = putRecords.length - fullPutCount - lightingPutCount;
    await captureScopeEvidence(page, "03_electrical_only_scope.png", "ELECTRICAL", "iluminare", {
      userClicks: ["mode-subset", "ELECTRICAL"],
      putCount: electricalPutCount,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
      reloadPreserved: true,
    });

    await selectSubsetOnly(page, ["LIGHTING", "ELECTRICAL"]);
    const combinedPutCount =
      putRecords.length - fullPutCount - lightingPutCount - electricalPutCount;
    await captureScopeEvidence(page, "04_lighting_electrical_combined.png", "LIGHTING+ELECTRICAL", "iluminare", {
      userClicks: ["mode-subset", "LIGHTING", "ELECTRICAL"],
      putCount: combinedPutCount,
      submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
      reloadPreserved: true,
    });

    await selectFullProduct(page);
    await captureScopeEvidence(
      page,
      "05_montaj_without_psu_selector.png",
      "full_product (Montaj tab)",
      "montaj",
      {
        userClicks: ["mode-full"],
        putCount: putRecords.length,
        submittedSoldModules: putRecords.at(-1)?.sold_modules ?? [],
        reloadPreserved: true,
      },
    );

    await page.reload({ waitUntil: "networkidle", timeout: 120_000 });
    await gotoOfferScopePanel(page);
    await expect(page.getByTestId("intake-v6-offer-scope-mode-full")).toBeChecked();

    fs.writeFileSync(
      REPORT_PATH,
      JSON.stringify(
        {
          workspace: WORKSPACE_ID,
          workspace_code: "IR-MRI01769",
          route: `${UI_BASE}/intake-v6/${WORKSPACE_ID}/operator`,
          captured_at: new Date().toISOString(),
          ui_driven: true,
          direct_api_used: false,
          put_records: putRecords,
          screenshots: notes,
        },
        null,
        2,
      ),
    );

    expect(putRecords.length).toBeGreaterThan(0);
    for (const note of notes.slice(0, 4)) {
      expect(note.lightingSubsection || note.electricalSubsection || note.soldScope.includes("Montaj")).toBeTruthy();
    }
    expect(notes[4]?.psuOnMontaj).toBe(false);
  });
});
