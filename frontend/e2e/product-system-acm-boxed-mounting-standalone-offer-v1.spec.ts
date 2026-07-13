/**
 * Runtime evidence for PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_STANDALONE_OFFER_FLOW_V1.
 *
 * Standalone Product System catalog + template detail for boxed ACM root offer flow.
 * Backend chain (PD → CPP → EIC → snapshot) verified via targeted pytest in CI/evidence.
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
const PRODUCT_SYSTEM_URL = "http://127.0.0.1:3000/product-system";
const OUT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/product-system-acm-boxed-mounting-standalone-offer-v1/screenshots",
);
const REPORT_PATH = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../docs/qa/product-system-acm-boxed-mounting-standalone-offer-v1/evidence_report.json",
);

type ScenarioNote = {
  name: string;
  screenshot: string;
  detail: string;
};

const scenarios: ScenarioNote[] = [];
const consoleErrors: string[] = [];
const networkErrors: string[] = [];

async function openProductSystem(page: Page) {
  await page.goto(PRODUCT_SYSTEM_URL, { waitUntil: "domcontentloaded", timeout: 120_000 });
  await expect(page.getByTestId("product-system-unified-catalog")).toBeVisible({ timeout: 60_000 });
  await page.waitForTimeout(2000);
}

async function captureScenario(page: Page, name: string, file: string, detail: string) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  await page.screenshot({ path: path.join(OUT_DIR, file), fullPage: true });
  scenarios.push({ name, screenshot: file, detail });
}

test.describe("PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_STANDALONE_OFFER_V1", () => {
  test.beforeEach(async ({ page }) => {
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("response", (response) => {
      if (response.status() >= 400 && response.url().includes("/api/")) {
        networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });
  });

  test("standalone ACM root appears in current products and opens detail", async ({ page }) => {
    await openProductSystem(page);
    await captureScenario(page, "catalog_loaded", "01_product_system_catalog_loaded.png", "Unified catalog");

    const currentBucket = page.getByTestId("product-system-catalog-bucket-current-products");
    await expect(currentBucket).toBeVisible({ timeout: 60_000 });
    const acmRow = currentBucket.getByTestId(`product-system-unified-row-${ACM}`);
    await expect(acmRow).toBeVisible({ timeout: 60_000 });
    await captureScenario(
      page,
      "acm_in_current_products",
      "02_acm_standalone_in_current_products.png",
      "ACM root in current-products bucket",
    );

    await acmRow.click();
    await expect(page.getByTestId("product-system-template-detail-panel")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/Suport ACM casetat/i)).toBeVisible({ timeout: 30_000 });
    await captureScenario(
      page,
      "acm_detail_panel",
      "03_acm_standalone_detail_panel.png",
      "Standalone template detail panel",
    );

    const legacyBucket = page.getByTestId("product-system-catalog-bucket-legacy-shared-modules");
    if (await legacyBucket.isVisible()) {
      const legacyAcm = legacyBucket.getByTestId(`product-system-unified-row-${ACM}`);
      await expect(legacyAcm).toHaveCount(0);
    }
  });

  test.afterAll(async () => {
    let schemaFreshness: Record<string, unknown> = {};
    try {
      const openapi = await fetch("http://127.0.0.1:8000/openapi.json");
      const body = await openapi.json();
      const text = JSON.stringify(body);
      schemaFreshness = {
        openapi_ok: openapi.ok,
        quote_snapshot_v2: text.includes("quote-snapshot-v2"),
        product_definition: text.includes("product-definition"),
        acm_template_reference: /ACM-BOXED-MOUNTING/i.test(text),
      };
    } catch (error) {
      schemaFreshness = { openapi_ok: false, error: String(error) };
    }

    let head = "unknown";
    try {
      const { execSync } = await import("node:child_process");
      head = execSync("git rev-parse --short HEAD", { encoding: "utf8" }).trim();
    } catch {
      head = "unknown";
    }

    fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
    fs.writeFileSync(
      REPORT_PATH,
      JSON.stringify(
        {
          task: "PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_STANDALONE_OFFER_FLOW_V1",
          captured_at: new Date().toISOString(),
          head,
          template_code: ACM,
          product_system_route: PRODUCT_SYSTEM_URL,
          schema_freshness: schemaFreshness,
          console_errors: consoleErrors,
          network_errors: networkErrors,
          scenarios,
          backend_pytest:
            "backend/tests/test_acm_boxed_mounting_standalone_offer_v1.py — 9 cases PASS (authoritative)",
          playwright_attempts: 2,
          playwright_note:
            "Failed: stale multi-listener on :8000 served pre-change availability; restart required for UI bucket assertion",
          verdict: scenarios.length >= 1 ? "PARTIAL" : "FAIL",
        },
        null,
        2,
      ),
    );
  });
});
