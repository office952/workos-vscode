import { expect, test } from "@playwright/test";

const WORKSPACE_ID = "b00a3a0c-5a3d-4d0b-a95e-582bb542dde1";
const WORKSPACE_ROUTE_CODE = "IR-MRI01769";
const UI_BASE = process.env.INTAKE_V6_UI_BASE ?? "http://127.0.0.1:3000";

async function resolveOperatorUrl(request: import("@playwright/test").APIRequestContext): Promise<string> {
  const byUuid = `${UI_BASE}/intake-v6/${WORKSPACE_ID}/operator`;
  const probe = await request.get(byUuid);
  if (probe.ok()) {
    return byUuid;
  }
  return `${UI_BASE}/intake-v6/${WORKSPACE_ROUTE_CODE}/operator`;
}

test("minimal offer-scope save clears saving state", async ({ page, request }) => {
  const operatorUrl = await resolveOperatorUrl(request);
  const puts: { status: number; body: string }[] = [];
  page.on("response", async (response) => {
    if (response.url().includes("/offer-scope") && response.request().method() === "PUT") {
      puts.push({
        status: response.status(),
        body: (await response.text()).slice(0, 400),
      });
    }
  });

  await page.goto(operatorUrl, { waitUntil: "networkidle", timeout: 120_000 });
  await page.getByTestId("intake-v6-progress-step-layers").click();
  await expect(page.getByTestId("intake-v6-offer-scope-panel")).toBeVisible({ timeout: 60_000 });

  if (!(await page.getByTestId("intake-v6-offer-scope-mode-full").isChecked())) {
    const fullPut = page.waitForResponse(
      (r) => r.url().includes("/offer-scope") && r.request().method() === "PUT" && r.ok(),
      { timeout: 120_000 },
    );
    await page.getByTestId("intake-v6-offer-scope-mode-full").click({ force: true });
    await fullPut;
  }

  await page.getByTestId("intake-v6-offer-scope-mode-subset").click();
  await expect(page.getByTestId("intake-v6-offer-scope-subset-options")).toBeVisible();
  const putPromise = page.waitForResponse(
    (r) => r.url().includes("/offer-scope") && r.request().method() === "PUT" && r.ok(),
    { timeout: 120_000 },
  );
  await page.getByTestId("intake-v6-offer-scope-back").check({ force: true });
  const putResp = await putPromise;
  expect(putResp.ok()).toBeTruthy();

  const status = page.getByTestId("intake-v6-offer-scope-status");
  await expect(status).not.toContainText("Salvez selecția", { timeout: 30_000 });
  await expect(status).toHaveText("Selecție confirmată", { timeout: 30_000 });

  expect(puts.length).toBeGreaterThanOrEqual(1);
});
