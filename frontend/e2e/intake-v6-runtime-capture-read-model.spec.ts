import { expect, test } from "@playwright/test";

const REVIEW_URL =
  "http://127.0.0.1:3000/intake-v6/668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c/operator";

const EXPECTED_FIELD_KEYS = [
  "svg.selected_layer_refs[]",
  "finish.finish_target",
  "finish.print_required",
  "finish.lamination_required",
  "mounting.mounting_scope",
  "support.support_type",
];

test.describe("Intake V6 runtime capture read model smoke", () => {
  test("review shows runtime capture panel with six read-only field rows", async ({ page }) => {
    await page.goto(REVIEW_URL, { waitUntil: "networkidle", timeout: 120_000 });

    await expect(page.getByTestId("intake-v6-step-review")).toBeVisible({ timeout: 60_000 });
    await expect(page.getByTestId("intake-v6-header-step")).toHaveText(/Review/i);

    const panel = page.getByTestId("runtime-capture-read-model-panel");
    await expect(panel).toBeVisible();
    await expect(panel).toHaveAttribute("data-read-only", "true");

    const fields = page.getByTestId("runtime-capture-read-model-fields");
    await expect(fields).toBeVisible();
    for (const fieldKey of EXPECTED_FIELD_KEYS) {
      await expect(fields).toContainText(fieldKey);
    }

    const rowCount = await fields.locator(':scope > div').count();
    expect(rowCount).toBe(6);

    await expect(panel.getByRole("button")).toHaveCount(0);
    await expect(panel.getByRole("textbox")).toHaveCount(0);
    await expect(panel.getByRole("combobox")).toHaveCount(0);
    await expect(panel.locator("input, textarea, select, [contenteditable='true']")).toHaveCount(0);
  });
});