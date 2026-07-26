import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const QA_SCREENSHOTS = path.resolve(
  process.cwd(),
  "../docs/qa/product-system-playwright-readonly-smoke-v1/screenshots",
);
const FACE_QA_SCREENSHOTS = path.resolve(
  process.cwd(),
  "../docs/qa/face-component-truth-workshop-v1/screenshots",
);

const LETTERS = "TPL-VOLUMETRIC-LETTERS_v2";
const LOGO = "TPL-VOLUMETRIC-LOGO_v1";
const COMPOSER = "TPL-LETTERS-COMPOSER_v1";
const LEGACY_FACE = "TPL-VOLUMETRIC-FACE_v1";

const COMPONENT_TEMPLATE_CODES = [
  "TPL-COMP-LETTER-FACE_v1",
  "TPL-COMP-LETTER-BACK_v1",
  "TPL-COMP-LETTER-RETURN-CANT_v1",
  "TPL-COMP-LETTER-LED_v1",
  "TPL-COMP-LETTER-FINISH_v1",
  "TPL-COMP-LETTER-MOUNTING_v1",
] as const;

async function saveScreenshot(page: Page, name: string, targetDir = QA_SCREENSHOTS) {
  await mkdir(targetDir, { recursive: true });
  await page.screenshot({
    path: path.join(targetDir, `${name}.png`),
    fullPage: false,
  });
}

function canonicalCard(page: Page, templateCode: string) {
  return page.locator(
    `[data-testid="product-system-canonical-catalog-card"][data-template-code="${templateCode}"]`,
  );
}

async function waitForCanonicalCatalog(page: Page) {
  await expect(page.getByTestId("product-system-unified-catalog")).toBeVisible({ timeout: 60_000 });
  await expect(page.getByTestId("product-system-unified-catalog")).toHaveAttribute(
    "data-catalog-variant",
    "canonical",
  );
}

async function openTemplateEditorFromCatalog(page: Page, templateCode: string) {
  await canonicalCard(page, templateCode).click();
  await expect(page.getByTestId("product-system-template-detail-panel")).toBeVisible({
    timeout: 15_000,
  });
  await page.getByTestId("product-system-template-detail-tab-dossier").click();
  await expect(page.getByTestId("product-system-template-detail-open-editor")).toBeVisible({
    timeout: 10_000,
  });
  await page.getByTestId("product-system-template-detail-open-editor").click();
}

async function openCandidateModuleProdusPanel(page: Page) {
  await page.getByTestId("product-system-canonical-filter-deprecated").click();
  await expect(canonicalCard(page, COMPOSER)).toBeVisible({ timeout: 15_000 });
  await openTemplateEditorFromCatalog(page, COMPOSER);
  await expect(page.getByTestId("product-system-candidate-module-letters-set")).toBeVisible({
    timeout: 15_000,
  });
}

async function assertNoDangerousActions(page: Page) {
  const dangerousPatterns = [
    /^activate$/i,
    /^promote$/i,
    /create quote/i,
    /expose to work intake/i,
    /make offerable/i,
    /activate logo/i,
    /seed live/i,
    /write product truth/i,
  ];

  for (const pattern of dangerousPatterns) {
    await expect(page.getByRole("button", { name: pattern })).toHaveCount(0);
  }

  const pageText = (await page.locator("body").innerText()).toLowerCase();
  expect(pageText).not.toMatch(/\bwi=true\b/);
  expect(pageText).not.toMatch(/\bpricing=true\b/);
  expect(pageText).not.toMatch(/\bpd=true\b/);
}

test.describe("Product System readonly smoke", () => {
  test("canonical catalog, candidate Module produs panel, and guardrails stay operator-safe", async ({
    page,
  }) => {
    await page.goto("/product-system/products", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await waitForCanonicalCatalog(page);
    await expect(page.getByRole("heading", { name: /Product System/i })).toBeVisible();
    await expect(page.locator('[data-testid="product-system-unified-catalog"]')).not.toHaveText(
      /something went wrong|error boundary/i,
    );

    // Legacy five-bucket UI must stay gone (Nivel 2A/2B).
    await expect(page.getByTestId("product-system-catalog-bucket-current-products")).toHaveCount(0);
    await expect(page.getByTestId("product-system-catalog-bucket-candidate-module-sets")).toHaveCount(0);
    await expect(page.getByTestId("product-system-unified-row-candidate-set")).toHaveCount(0);

    await saveScreenshot(page, "01_product_system_loaded");

    await expect(canonicalCard(page, LETTERS)).toBeVisible({ timeout: 30_000 });
    await canonicalCard(page, LETTERS).click();
    await expect(page.getByTestId("product-system-template-detail-panel")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("product-system-template-detail-overview")).toHaveText(/Work Intake/i);

    await saveScreenshot(page, "02_active_root_assertions_visible");
    await saveScreenshot(page, "06_active_root_offerable_work_intake", FACE_QA_SCREENSHOTS);

    // Logo is advanced/hidden from the default operator list — open via All filter when present.
    await page.getByTestId("product-system-canonical-filter-all").click();
    const logoCard = canonicalCard(page, LOGO);
    if ((await logoCard.count()) > 0) {
      await logoCard.click();
      await expect(page.getByTestId("product-system-template-detail-panel")).toBeVisible({
        timeout: 15_000,
      });
      await expect(page.getByTestId("product-system-template-detail-overview")).not.toHaveText(
        /Work Intake DA/i,
      );
      await saveScreenshot(page, "03_logo_candidate_safe");
      await saveScreenshot(page, "07_logo_not_work_intake_owner_go", FACE_QA_SCREENSHOTS);
    }

    await openCandidateModuleProdusPanel(page);

    const candidateModuleProdusPanel = page.getByTestId("product-system-candidate-module-letters-set");
    await expect(candidateModuleProdusPanel).toHaveText(/Candidate Module produs|Module produs/i);
    await expect(candidateModuleProdusPanel).toHaveText(/Product Composer|Composer/i);
    await expect(candidateModuleProdusPanel).toHaveText(/Readonly|READONLY/i);
    await expect(candidateModuleProdusPanel).toHaveText(/NOT OFFERABLE|Not offerable/i);
    await expect(page.getByTestId("product-system-candidate-module-completeness-count")).toHaveText(
      /Live rows:\s*\d+\/7/i,
    );
    await expect(page.getByTestId("product-system-candidate-module-dossier-contract-summary")).toHaveText(
      /Dossier contract:\s*7\/7/i,
    );

    await page.getByTestId("product-system-candidate-module-tab-components").click();
    const componentsTable = page.getByTestId("product-system-candidate-module-components-table");
    await expect(componentsTable).toBeVisible({ timeout: 10_000 });
    for (const templateCode of COMPONENT_TEMPLATE_CODES) {
      await expect(componentsTable).toContainText(templateCode);
    }

    await page.getByTestId("product-system-candidate-module-tab-guards-audit").click();
    const guardLabels = page.getByTestId("product-system-candidate-module-inert-guard-labels");
    await expect(guardLabels).toBeVisible({ timeout: 10_000 });
    await expect(guardLabels).toHaveText(/Work Intake exposure:\s*blocked/i);
    await expect(guardLabels).toHaveText(/Pricing activation:\s*blocked/i);
    await expect(guardLabels).toHaveText(/ProductDefinition runtime:\s*blocked/i);
    await expect(guardLabels).toHaveText(/ProductAggregate runtime:\s*blocked/i);
    await expect(guardLabels).toHaveText(/Quote\/Order\/Execution:\s*blocked/i);

    const workshop = page.getByTestId("product-system-truth-owner-workshop");
    await expect(workshop).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("product-system-truth-workshop-global-status")).toHaveText(
      /OWNER INPUT REQUIRED/i,
    );
    await expect(workshop).toHaveText(/RETURN-CANT/i);
    await expect(workshop).toHaveText(/Culoare Stock/i);
    await expect(workshop).toHaveText(/Oracal/i);
    await expect(workshop).toHaveText(/Vopsit RAL/i);
    await expect(workshop).toHaveText(/No Product Truth write/i);
    await expect(workshop).toHaveText(/No Pricing activation/i);
    await expect(workshop).toHaveText(/No Work Intake exposure/i);
    await expect(workshop).toHaveText(/Întrebări pentru owner/i);
    await expect(page.getByTestId("product-system-return-cant-owner-inputs")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("product-system-return-cant-confirmed-so-far")).toHaveText(/Confirmed so far/i);
    await expect(page.getByTestId("product-system-return-cant-partial-so-far")).toHaveText(/Partial confirmed/i);
    await expect(page.getByTestId("product-system-return-cant-missing-before-pricing")).toHaveText(
      /Still missing before pricing/i,
    );
    await expect(page.getByTestId("product-system-return-cant-missing-before-product-definition")).toHaveText(
      /Still missing before ProductDefinition/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-oracal_selector_mode")).toHaveText(
      /listă completă Oracal/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-oracal_pricing_mode")).toHaveText(
      /preț pe cod\/familie/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-ral_input_mode")).toHaveText(
      /selector standard RAL/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-return_depths_standard")).toHaveText(
      /30 mm.*60 mm.*80 mm.*100 mm/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-return_material")).toHaveText(
      /aluminiu 0\.6 mm/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-return_material_unit")).toHaveText(/^ml$/i);
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-return_labor_unit")).toHaveText(/^ml$/i);
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-stock_color_affects_price")).toHaveText(
      /Nu — doar informație atelier/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-perimeter_geometry_source")).toHaveText(
      /perimetru\/contur real/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-ral_material_price_rule")).toHaveText(
      /MAT-VOPSEA-RAL-CANT-30MM/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-ral_material_price_rule")).toHaveText(
      /\/inventory\/pricing/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-ral_labor_price_rule")).toHaveText(
      /RETURN_CANT_RAL_PAINT_LABOR/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-ral_labor_price_rule")).toHaveText(
      /\/inventory\/pricing/i,
    );
    await expect(page.getByTestId("product-system-return-cant-owner-input-value-oracal_code_list")).toHaveText(
      /Intake V6 colorRegistry/i,
    );
    const returnCantPanel = page.getByTestId("product-system-return-cant-owner-inputs");
    await expect(returnCantPanel).not.toHaveText(/ORACAL-\d+/i);
    await expect(page.getByRole("button", { name: /^save$/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /write product truth/i })).toHaveCount(0);

    const catalogPricePanel = page.getByTestId("product-system-return-cant-catalog-price-inputs");
    await expect(catalogPricePanel).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("product-system-return-cant-catalog-price-global-status")).toHaveText(
      /NOT READY FOR PRICING/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-ready-for-pricing")).toHaveText(
      /Ready for pricing: NO/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-known-oracal_catalog_source")).toHaveText(
      /Intake V6/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-known-ral_catalog_source")).toHaveText(
      /Intake V6|ralColors/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-known-oracal_selector_source")).toHaveText(
      /Intake V6|color registry/i,
    );
    await expect(page.getByTestId("product-system-return-cant-oracal-pricing-source")).toHaveText(
      /\/inventory\/pricing/i,
    );
    await expect(page.getByTestId("product-system-return-cant-oracal-series-price-651")).toHaveText(
      /MAT-ORACAL-651/i,
    );
    await expect(page.getByTestId("product-system-return-cant-oracal-series-price-641")).toHaveText(
      /MAT-ORACAL-641/i,
    );
    await expect(page.getByTestId("product-system-return-cant-oracal-series-price-8500")).toHaveText(
      /MAT-ORACAL-8500/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-value-oracal_calculation_model")).toHaveText(
      /lățime rolă.*lungime folosită|mp/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-value-oracal_roll_widths")).toHaveText(
      /100 cm.*126 cm/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-value-oracal_price_table")).toHaveText(
      /651\/641\/8500 confirmate|restul codurilor/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-known-oracal_price_mode")).toHaveText(
      /preț.*cod\/familie/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-value-ral_selector_source")).toHaveText(
      /RAL Classic/i,
    );
    await expect(page.getByTestId("product-system-return-cant-ral-pricing-source")).toHaveText(
      /\/inventory\/pricing/i,
    );
    await expect(page.getByTestId("product-system-return-cant-ral-material-price-30")).toHaveText(
      /MAT-VOPSEA-RAL-CANT-30MM/i,
    );
    await expect(page.getByTestId("product-system-return-cant-ral-material-price-60")).toHaveText(
      /MAT-VOPSEA-RAL-CANT-60MM/i,
    );
    await expect(page.getByTestId("product-system-return-cant-ral-material-price-80")).toHaveText(
      /MAT-VOPSEA-RAL-CANT-80MM/i,
    );
    await expect(page.getByTestId("product-system-return-cant-ral-material-price-100")).toHaveText(
      /MAT-VOPSEA-RAL-CANT-100MM/i,
    );
    await expect(page.getByTestId("product-system-return-cant-ral-labor-price")).toHaveText(
      /RETURN_CANT_RAL_PAINT_LABOR/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-value-ral_material_price_by_depth")).toHaveText(
      /MAT-VOPSEA-RAL-CANT-30MM/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-value-ral_labor_price_by_depth")).toHaveText(
      /RETURN_CANT_RAL_PAINT_LABOR/i,
    );
    await expect(page.getByTestId("product-system-return-cant-ral-minimum-policy")).toHaveText(/100 lei/i);
    await expect(page.getByTestId("product-system-return-cant-ral-minimum-policy")).toHaveText(
      /owner commercial rule/i,
    );
    await expect(page.getByTestId("product-system-return-cant-ral-minimum-policy")).toHaveText(
      /NOT in Pricing Registry/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-value-ral_minimum_rule")).toHaveText(
      /100 lei/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-value-ral_minimum_rule")).toHaveText(
      /pe culoare RAL/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-value-ral_minimum_rule")).toHaveText(
      /total material RAL \+ manoperă/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-known-ral_minimum_rule")).toHaveText(
      /fără conversie automată/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-blockers")).not.toHaveText(
      /RAL minimum scope unresolved/i,
    );
    await expect(
      page.getByTestId("product-system-return-cant-catalog-price-value-return_material_depth_compatibility"),
    ).toHaveText(/aluminiu 0\.6 mm/i);
    await expect(catalogPricePanel).toHaveText(/MAT-ORACAL-641/);
    await expect(catalogPricePanel).toHaveText(/\/inventory\/pricing/i);
    await expect(catalogPricePanel).not.toHaveText(/8\.00 EUR\/mp|5\.00 EUR\/mp|13\.00 EUR\/mp/i);
    await expect(catalogPricePanel).not.toHaveText(/2\.00 EUR\/ml|2\.50 EUR\/ml|3\.00 EUR\/ml|4\.00 EUR\/ml|1\.00 EUR\/ml/i);
    await expect(page.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveText(
      /No Product Truth live write/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveText(
      /No Pricing activation/i,
    );
    await expect(page.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveText(
      /No Work Intake exposure/i,
    );
    await saveScreenshot(page, "08_return_cant_still_intact", FACE_QA_SCREENSHOTS);

    const faceWorkshop = page.getByTestId("product-system-face-truth-workshop");
    await faceWorkshop.scrollIntoViewIfNeeded();
    await expect(faceWorkshop).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("product-system-face-truth-readonly-badge")).toHaveText(/READONLY/i);
    await expect(page.getByTestId("product-system-face-truth-not-ready-pricing-badge")).toHaveText(
      /NOT READY FOR PRICING/i,
    );
    await expect(page.getByTestId("product-system-face-truth-product-truth-blocked")).toHaveText(
      /Product Truth write blocked/i,
    );
    await expect(page.getByTestId("product-system-face-truth-finish-depends-badge")).toHaveText(
      /FINISH depends on FACE boundary/i,
    );
    await expect(page.getByTestId("product-system-face-truth-vector-litere")).toHaveText(/Vector Litere/i);
    await expect(page.getByTestId("product-system-face-truth-downstream-mp_face_area")).toHaveText(/mp_face_area/i);
    await expect(page.getByTestId("product-system-face-truth-return-cant-perimeter")).toHaveText(
      /RETURN-CANT consumes.*perimeter/i,
    );
    await expect(page.getByTestId("product-system-face-truth-finish-face-area")).toHaveText(
      /FINISH consumes mp_face_area/i,
    );
    await expect(page.getByTestId("product-system-face-truth-ready-for-pricing")).toHaveText(/Ready for pricing: NO/i);
    await expect(page.getByTestId("product-system-face-truth-readiness-blockers")).toBeVisible();
    await expect(page.getByTestId("product-system-face-truth-retired-finish-paths")).toHaveText(
      /product\.components\.finish\.oracal_code/i,
    );
    await expect(page.getByRole("button", { name: /^apply$/i })).toHaveCount(0);

    await saveScreenshot(page, "01_face_workshop_panel", FACE_QA_SCREENSHOTS);
    await saveScreenshot(page, "02_face_owns_does_not_own", FACE_QA_SCREENSHOTS);
    await page.getByTestId("product-system-face-truth-geometry-source").scrollIntoViewIfNeeded();
    await saveScreenshot(page, "03_geometry_downstream_outputs", FACE_QA_SCREENSHOTS);
    await page.getByTestId("product-system-face-truth-readiness-blockers").scrollIntoViewIfNeeded();
    await saveScreenshot(page, "04_owner_input_blockers", FACE_QA_SCREENSHOTS);
    await saveScreenshot(page, "05_no_dangerous_actions", FACE_QA_SCREENSHOTS);

    await saveScreenshot(page, "04_candidate_module_guards_blocked");

    // Legacy replacement readiness lives on Internal Module produs → Guards (no bucket UI).
    await page.goto("/product-system/products", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await waitForCanonicalCatalog(page);
    await page.getByTestId("product-system-canonical-filter-internal").click();
    await expect(canonicalCard(page, LEGACY_FACE)).toBeVisible({ timeout: 15_000 });
    await canonicalCard(page, LEGACY_FACE).click();
    await expect(page.getByTestId("product-system-template-detail-panel")).toBeVisible({
      timeout: 15_000,
    });
    await page.getByTestId("product-system-template-detail-tab-guards").click();
    await expect(page.getByTestId("product-system-legacy-replacement-readiness")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("product-system-legacy-replacement-global-verdict")).toHaveText(
      /NOT READY FOR DELETE/i,
    );
    await expect(page.getByTestId("product-system-legacy-replacement-summary-delete-ready-count")).toHaveText("0");
    const replacementTable = page.getByTestId("product-system-legacy-replacement-table");
    await expect(replacementTable).toContainText("TPL-VOLUMETRIC-FACE_v1");
    await expect(replacementTable).toContainText("TPL-COMP-LETTER-FACE_v1");
    await expect(replacementTable).toContainText("TPL-VOLUMETRIC-LED_v1");
    await expect(replacementTable).toContainText("TPL-COMP-LETTER-LED_v1");
    await expect(replacementTable).toContainText("TPL-VOLUM-ALUMINIU_v1");
    await expect(replacementTable).toContainText("TPL-COMP-LETTER-RETURN-CANT_v1");

    await saveScreenshot(page, "06_legacy_replacement_readiness");

    await openCandidateModuleProdusPanel(page);
    await expect(page.getByTestId("product-system-candidate-module-replacement-context")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId("product-system-candidate-module-replacement-context")).toHaveText(
      /Nu înlocuiește runtime acum|replacement map readonly/i,
    );
    await expect(page.getByTestId("product-system-candidate-module-replaces-face")).toBeVisible();

    await saveScreenshot(page, "07_candidate_module_replacement_context");

    const pageText = (await page.locator("body").innerText()).toLowerCase();
    expect(pageText).not.toMatch(/ready to delete/);
    await expect(page.getByRole("button", { name: /^delete now$/i })).toHaveCount(0);

    await assertNoDangerousActions(page);
  });
});
