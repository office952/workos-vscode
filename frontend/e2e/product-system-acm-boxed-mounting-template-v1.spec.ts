/**
 * Runtime evidence for PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_TEMPLATE_V1.
 *
 * Flow A: standalone Product System template visibility
 * Flow B: Intake V6 linked child via mounting preparation selector
 */
import { expect, test } from "@playwright/test";

const METAL = "TPL-METAL-PREMOUNT-STRUCTURE_v1";
const ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";

test.describe("Product System ACM boxed mounting template v1", () => {
  test("Flow A — standalone template appears in Product System", async ({ page }) => {
    await page.goto(`/product-system?template=${encodeURIComponent(ACM)}`);
    await expect(page.getByText(ACM, { exact: false })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/casetat|ACM/i).first()).toBeVisible();
  });

  test("Flow B — Intake V6 mounting selector offers ACM boxed support", async ({ page }) => {
    test.skip(!process.env.PW_INTAKE_V6_WORKSPACE_ID, "Set PW_INTAKE_V6_WORKSPACE_ID for linked-child flow");

    const workspaceId = process.env.PW_INTAKE_V6_WORKSPACE_ID as string;
    await page.goto(`/intake-v6/${workspaceId}`);
    await page.getByTestId("intake-v6-mounting-solution-selector").selectOption(ACM);
    await expect(page.getByTestId("intake-v6-mounting-acm-panel_width_mm")).toBeVisible();
    await expect(page.getByText(`Template: ${ACM}`)).toBeVisible();

    // Metal premount regression spot-check — selector still lists metal option
    await page.getByTestId("intake-v6-mounting-solution-selector").selectOption(METAL);
    await expect(page.getByTestId("intake-v6-mounting-solution-bar-material")).toBeVisible();
  });
});
