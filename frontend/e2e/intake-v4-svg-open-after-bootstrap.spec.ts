/**

 * Intake V4 — post-Open SVG load after workspace bootstrap.

 *

 * Prerequisites:

 *   - Full dev stack (scripts/start-dev.ps1) — backend :8000 + frontend :3000

 *   - PW_SKIP_WEB_SERVER=1 when stack already running

 *   - npx playwright install chromium

 */

import { expect, test, type Page } from "@playwright/test";

import fs from "node:fs";

import path from "node:path";

import { fileURLToPath } from "node:url";



import { createIntakeV4WorkspaceForE2e, probeIntakeV4LiveBackend } from "./helpers/intakeV4Live";



const __dirname = path.dirname(fileURLToPath(import.meta.url));

const FIXTURE_SVG = path.join(__dirname, "fixtures", "workos-geometry-smoke.svg");

const FIXTURE_BASENAME = "workos-geometry-smoke.svg";



let skipReason: string | undefined;



async function waitForAuthGate(page: Page) {

  await expect(page.getByText("Se verifică sesiunea")).toHaveCount(0, { timeout: 45_000 });

}



async function waitForV4WorkspaceReady(page: Page) {

  await page.waitForSelector('[data-testid="intake-v4-operator-workspace"]', { timeout: 60_000 });

  await expect(page.getByText("Loading workspace…")).toHaveCount(0, { timeout: 60_000 });

  const fileInput = page.getByTestId("intake-v4-svg-input");

  await fileInput.waitFor({ state: "attached", timeout: 30_000 });

  return fileInput;

}



async function assertSvgOpenPostSelect(page: Page) {

  await expect(page.getByTestId("intake-v4-current-file")).toContainText(FIXTURE_BASENAME, {

    timeout: 20_000,

  });

  await expect(page.getByTestId("intake-v4-svg-preview")).toBeVisible({ timeout: 20_000 });

  await expect(page.getByTestId("intake-v4-analysis-summary")).toBeVisible({ timeout: 20_000 });

  await expect(page.getByTestId("intake-v4-layer-table")).toBeVisible({ timeout: 20_000 });

  await expect(page.getByTestId("intake-v4-error")).toHaveCount(0);

}



/** Simulates OS drag-drop onto the V4 workspace shell (same handler as browse). */

async function dropSvgOnV4Workspace(page: Page, fixturePath: string, basename: string) {

  const b64 = fs.readFileSync(fixturePath).toString("base64");

  const dataTransfer = await page.evaluateHandle(

    ({ name, type, payloadB64 }) => {

      const bin = atob(payloadB64);

      const arr = new Uint8Array(bin.length);

      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);

      const dt = new DataTransfer();

      dt.items.add(new File([arr], name, { type }));

      return dt;

    },

    { name: basename, type: "image/svg+xml", payloadB64: b64 },

  );

  await page.getByTestId("intake-v4-operator-workspace-file-drop").dispatchEvent("drop", {

    dataTransfer,

  });

}



test.describe("Intake V4 SVG Open after bootstrap", () => {

  test.beforeAll(async () => {

    const probe = await probeIntakeV4LiveBackend();

    if (!probe.backendHealthy) {

      skipReason = probe.reason ?? "Intake V4 live backend unavailable";

    }

  });



  test.beforeEach(() => {

    test.skip(Boolean(skipReason), skipReason);

  });



  test("standalone route keeps /intake-v4-app prefix and shows preview after Open", async ({

    page,

  }) => {

    test.setTimeout(120_000);



    await page.goto("/intake-v4-app/operator");

    await waitForAuthGate(page);

    await page.waitForURL(/\/intake-v4-app\/[0-9a-f-]+\/operator/i, { timeout: 60_000 });



    await expect(page.getByTestId("intake-v4-standalone-root")).toBeVisible();

    await expect(page.getByTestId("workos-desktop-shell")).toHaveCount(0);



    const fileInput = await waitForV4WorkspaceReady(page);

    await fileInput.setInputFiles(FIXTURE_SVG);

    await assertSvgOpenPostSelect(page);

  });



  test("shell route loads SVG after Open on /intake-v4/operator", async ({ page }) => {

    test.setTimeout(120_000);



    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-v4-shell");

    await page.goto(`/intake-v4/${workspaceId}/operator`);

    await waitForAuthGate(page);

    expect(page.url()).not.toContain("/intake-v4-app/");



    await expect(page.getByTestId("workos-desktop-shell")).toBeVisible();



    const fileInput = await waitForV4WorkspaceReady(page);

    await fileInput.setInputFiles(FIXTURE_SVG);

    await assertSvgOpenPostSelect(page);

  });



  test("standalone route loads SVG via drag-drop on file-drop shell", async ({ page }) => {

    test.setTimeout(120_000);



    const workspaceId = await createIntakeV4WorkspaceForE2e("e2e-v4-drop");

    await page.goto(`/intake-v4-app/${workspaceId}/operator`);

    await waitForAuthGate(page);



    await waitForV4WorkspaceReady(page);

    await dropSvgOnV4Workspace(page, FIXTURE_SVG, FIXTURE_BASENAME);

    await assertSvgOpenPostSelect(page);

    await expect(page.getByTestId("intake-v4-operator-workspace-file-drop-notice")).toContainText(

      FIXTURE_BASENAME,

      { timeout: 10_000 },

    );

  });

});

