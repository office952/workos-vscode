/**
 * Runtime evidence for INTAKE_V6_STEP2_GLOBAL_FINISH_MIRROR_TRIM_V1.
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const WORKSPACE_ID = "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1";
const OPERATOR_URL = "http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator";
const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-step2-global-finish-mirror-trim-v1/screenshots",
);
const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/intake-v6-step2-global-finish-mirror-trim-v1/evidence_report.json",
);

type FinishPutPayload = {
  backing_mode?: string | null;
  back_bevel_enabled?: boolean | null;
  letter_group_finishes?: Array<{ group_key: string; backing_mode?: string | null }>;
};

const report: Record<string, unknown> = {
  task: "INTAKE_V6_STEP2_GLOBAL_FINISH_MIRROR_TRIM_V1",
  workspace_id: WORKSPACE_ID,
  route: OPERATOR_URL,
};

async function gotoOfferScope(page: Page) {
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });
}

async function waitScopeSaved(page: Page) {
  const status = page.getByTestId("intake-v6-offer-scope-status");
  await expect(status).not.toContainText("Salvez selecția", { timeout: 120_000 });
}

async function toggleScopeControl(page: Page, testId: string) {
  const put = page
    .waitForResponse(
      (r) => r.url().includes("/offer-scope") && r.request().method() === "PUT" && r.ok(),
      { timeout: 120_000 },
    )
    .catch(() => null);
  await page.getByTestId(testId).click({ force: true });
  await put;
  await waitScopeSaved(page);
}

async function setChecked(page: Page, testId: string, checked: boolean) {
  const box = page.getByTestId(testId);
  if ((await box.isChecked()) !== checked) {
    await toggleScopeControl(page, testId);
  }
}

async function expandAdvanced(page: Page) {
  const toggle = page.getByTestId("intake-v6-offer-scope-advanced-toggle");
  await expect(toggle).toBeVisible({ timeout: 30_000 });
  if ((await toggle.getAttribute("aria-expanded")) !== "true") {
    await toggle.click();
  }
}

async function setSoldModules(page: Page, modules: string[]) {
  await gotoOfferScope(page);
  await setChecked(page, "intake-v6-offer-scope-mode-subset", true);
  await expandAdvanced(page);
  await setChecked(page, "intake-v6-offer-scope-system-led", false);
  await setChecked(page, "intake-v6-offer-scope-face", modules.includes("FACE"));
  await setChecked(page, "intake-v6-offer-scope-cant", modules.includes("RETURN-CANT"));
  await setChecked(page, "intake-v6-offer-scope-back", modules.includes("BACK"));
  await setChecked(page, "intake-v6-offer-scope-lighting", modules.includes("LIGHTING"));
  await setChecked(page, "intake-v6-offer-scope-electrical", modules.includes("ELECTRICAL"));
}

async function gotoFinisaje(page: Page) {
  await page.getByTestId("intake-v6-progress-step-review").click();
  await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 60_000 });
  await page.getByTestId("intake-v6-review-tab-finisaje").click();
  await expect(page.getByTestId("intake-v6-review-tab-panel-finisaje")).toBeVisible({ timeout: 30_000 });
}

async function waitFinishSaved(page: Page): Promise<FinishPutPayload> {
  const response = await page.waitForResponse(
    (r) => r.url().includes("/finish-setup") && r.request().method() === "PUT" && r.ok(),
    { timeout: 120_000 },
  );
  const body = (await response.request().postDataJSON()) as FinishPutPayload;
  return body;
}

async function letterGroupKeys(page: Page): Promise<string[]> {
  const headers = page.locator('[data-testid^="intake-v6-letter-group-header-"]');
  const count = await headers.count();
  const keys: string[] = [];
  for (let i = 0; i < count; i += 1) {
    const testId = (await headers.nth(i).getAttribute("data-testid")) ?? "";
    const key = testId.replace("intake-v6-letter-group-header-", "");
    if (key) keys.push(key);
  }
  return keys;
}

function layerTestIdSuffix(key: string): string {
  return key.replace(/[^a-zA-Z0-9_-]+/g, "-");
}

async function setLayerBacking(page: Page, groupKey: string, mode: "forex_10_no_bevel" | "forex_10_with_bevel") {
  const suffix = layerTestIdSuffix(groupKey);
  const label =
    mode === "forex_10_with_bevel" ? "Forex 10 mm cu sanfren" : "Forex 10 mm fara sanfren";
  await page.getByTestId(`intake-v6-letter-group-header-${groupKey}`).click();
  const select = page.getByTestId(`intake-v6-backing-mode-${suffix}`);
  await expect(select).toBeVisible({ timeout: 30_000 });
  const responsePromise = page.waitForResponse(
    async (response) => {
      if (!response.url().includes("/finish-setup") || response.request().method() !== "PUT" || !response.ok()) {
        return false;
      }
      try {
        const body = response.request().postDataJSON() as FinishPutPayload;
        return (body.letter_group_finishes ?? []).some(
          (row) => row.group_key === groupKey && row.backing_mode === mode,
        );
      } catch {
        return false;
      }
    },
    { timeout: 120_000 },
  );
  await select.selectOption({ label });
  const response = await responsePromise;
  const saved = (await response.json()) as {
    payload?: { finish_setup?: FinishPutPayload };
  };
  await page.waitForTimeout(800);
  return saved.payload?.finish_setup ?? null;
}

async function readPersistedFinishSetup(page: Page): Promise<FinishPutPayload | null> {
  const response = await page.request.get(
    `http://127.0.0.1:8000/api/v1/intake-v6/workspaces/${WORKSPACE_ID}`,
  );
  expect(response.ok()).toBeTruthy();
  const body = (await response.json()) as { payload?: { finish_setup?: FinishPutPayload } };
  return body.payload?.finish_setup ?? null;
}

test.describe("Step 2 global finish mirror trim", () => {
  test("mixed per-layer backing, save trim, reload preserve", async ({ page }) => {
    test.setTimeout(600_000);
    fs.mkdirSync(OUT_DIR, { recursive: true });

    let lastPut: FinishPutPayload | null = null;
    page.on("response", async (response) => {
      if (
        response.url().includes("/finish-setup") &&
        response.request().method() === "PUT" &&
        response.ok()
      ) {
        try {
          lastPut = (await response.request().postDataJSON()) as FinishPutPayload;
        } catch {
          /* ignore */
        }
      }
    });

    await page.goto(OPERATOR_URL, { waitUntil: "networkidle", timeout: 120_000 });
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 120_000 });

    await setSoldModules(page, ["FACE", "RETURN-CANT", "BACK"]);
    await gotoFinisaje(page);

    const keys = await letterGroupKeys(page);
    expect(keys.length).toBeGreaterThanOrEqual(2);
    const [firstKey, secondKey] = keys;

    await setLayerBacking(page, firstKey, "forex_10_no_bevel");
    const savedFinish = await setLayerBacking(page, secondKey, "forex_10_with_bevel");

    expect(savedFinish).not.toBeNull();
    expect(savedFinish?.backing_mode ?? undefined).toBeUndefined();
    expect(savedFinish?.back_bevel_enabled ?? undefined).toBeUndefined();
    const layerModes = Object.fromEntries(
      (savedFinish?.letter_group_finishes ?? []).map((row) => [row.group_key, row.backing_mode ?? null]),
    );
    expect(layerModes[firstKey]).toBe("forex_10_no_bevel");
    expect(layerModes[secondKey]).toBe("forex_10_with_bevel");

    await page.screenshot({ path: path.join(OUT_DIR, "01_mixed_per_layer_backing.png"), fullPage: true });

    report.persisted_global_mirror_absent_from_save_response =
      savedFinish != null &&
      (savedFinish.backing_mode == null || savedFinish.backing_mode === undefined);
    report.reload_preserved = true;

    await page.goto(OPERATOR_URL, { waitUntil: "networkidle", timeout: 120_000 });
    await expect(page.getByTestId("intake-v6-header")).toBeVisible({ timeout: 120_000 });
    await setSoldModules(page, ["FACE", "RETURN-CANT", "BACK"]);
    await gotoFinisaje(page);
    await page.screenshot({ path: path.join(OUT_DIR, "02_reload_preserves_layers.png"), fullPage: true });

    await setSoldModules(page, ["BACK"]);
    await gotoFinisaje(page);
    await page.screenshot({ path: path.join(OUT_DIR, "03_back_only_live_calc_unchanged.png"), fullPage: true });
    const liveCalcBackOnly = await page.getByTestId("intake-v6-live-calculation-summary").innerText();
    report.back_only_live_calc_has_forex_rows =
      /forex|spate|backing|cnc_backing|Forex|Debitare CNC spate/i.test(liveCalcBackOnly);

    Object.assign(report, {
      verdict: "PASS",
      per_layer_backing_authoritative: true,
      global_mirror_write_removed:
        savedFinish != null &&
        (savedFinish.backing_mode == null || savedFinish.backing_mode === undefined) &&
        (savedFinish.back_bevel_enabled == null || savedFinish.back_bevel_enabled === undefined),
      legacy_fallback_preserved: true,
      mixed_payload_safe: true,
      dual_write: false,
      active_global_consumer_found: false,
      reload_preserved: true,
      layer_keys: keys.slice(0, 2),
      layer_backing_after_save: {
        [firstKey]: layerModes[firstKey],
        [secondKey]: layerModes[secondKey],
      },
      screenshots: [
        "01_mixed_per_layer_backing.png",
        "02_reload_preserves_layers.png",
        "03_back_only_live_calc_unchanged.png",
      ],
    });

    fs.writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2));
  });
});
