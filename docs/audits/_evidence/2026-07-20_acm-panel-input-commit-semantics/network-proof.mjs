/**
 * Runtime network proof — ACM_PANEL_OPERATOR_INPUT_COMMIT_SEMANTICS_V1
 * Fixture IV6-DB2F86B7 @ 1440x900
 */
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = process.env.PW_BASE_URL ?? "http://127.0.0.1:3000";
const BACKEND = process.env.PW_BACKEND_URL ?? "http://127.0.0.1:8003";
const ID = "a7b0162b-dc91-467f-aa24-c1279fb3a073";
const OUT = __dirname;

async function getL1() {
  const ws = await (await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${ID}`)).json();
  return ws.payload?.finish_setup?.acm_panel_instance?.configuration?.l1_mm ?? null;
}

async function main() {
  fs.mkdirSync(path.join(OUT, "shots"), { recursive: true });
  const cases = [];
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => sessionStorage.setItem("WORKOS_DEV_GUARD_BYPASS", "1"));
  const page = await ctx.newPage();
  const puts = [];
  page.on("request", (req) => {
    if (req.method() === "PUT" && /finish-setup/.test(req.url())) {
      let l1 = null;
      let domainAction = null;
      let authL1 = null;
      try {
        const j = JSON.parse(req.postData() || "{}");
        const inst = j.acm_panel_instance;
        l1 = inst?.configuration?.l1_mm ?? null;
        domainAction = j.acm_panel_domain_action ?? null;
        authL1 = inst?.configuration?.field_authority?.l1_mm ?? null;
      } catch {
        /* ignore */
      }
      puts.push({ t: Date.now(), l1, domainAction, authL1, phase: page._phase || "?" });
    }
  });

  await page.goto(`${UI}/intake-v6/${ID}/operator`, {
    waitUntil: "domcontentloaded",
    timeout: 120000,
  });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  await page.getByTestId("intake-v6-progress-step-review").click().catch(() => {});
  await page.getByTestId("intake-v6-step-review").waitFor({ state: "visible", timeout: 60000 });
  await page.getByTestId("intake-v6-product-component-row-acm_panel").click();
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(OUT, "shots", "01-before.png") });

  const openConstruction = async () => {
    const sec = page.getByTestId("intake-v6-acm-section-construction");
    if ((await sec.getAttribute("data-open")) !== "true") {
      await sec.locator("button").first().click();
      await page.waitForTimeout(200);
    }
  };
  await openConstruction();

  const runCase = async (name, fn) => {
    page._phase = name;
    const before = puts.length;
    const l1Before = await getL1();
    await fn();
    await page.waitForTimeout(900);
    const slice = puts.slice(before);
    const l1After = await getL1();
    cases.push({
      name,
      keystrokes: name,
      requestCount: slice.length,
      puts: slice,
      l1Before,
      l1After,
      duplicate: slice.length > 1,
    });
  };

  await runCase("typing_65", async () => {
    const input = page.getByTestId("intake-v6-acm-field-l1_mm");
    await input.click();
    await input.fill("");
    await input.type("65", { delay: 40 });
    await page.waitForTimeout(700);
  });

  await runCase("paste_75", async () => {
    const input = page.getByTestId("intake-v6-acm-field-l1_mm");
    await input.fill("75");
    await input.blur();
    await page.waitForTimeout(200);
  });

  await runCase("rapid_replace_78", async () => {
    const input = page.getByTestId("intake-v6-acm-field-l1_mm");
    await input.fill("7");
    await input.fill("78");
    await page.waitForTimeout(700);
  });

  await runCase("blur_commit_79", async () => {
    const input = page.getByTestId("intake-v6-acm-field-l1_mm");
    await input.fill("79");
    await input.blur();
  });

  await runCase("enter_commit_80", async () => {
    const input = page.getByTestId("intake-v6-acm-field-l1_mm");
    await input.fill("80");
    await input.press("Enter");
  });

  await runCase("section_switch_flush_81", async () => {
    const input = page.getByTestId("intake-v6-acm-field-l1_mm");
    await input.fill("81");
    await page.getByTestId("intake-v6-acm-section-geometry").locator("button").first().click();
  });

  await openConstruction();
  await runCase("confirm_with_pending_82", async () => {
    const input = page.getByTestId("intake-v6-acm-field-l1_mm");
    await input.fill("82");
    await page.getByTestId("intake-v6-acm-confirm-construction").click();
  });

  await openConstruction();
  await runCase("two_fields_flush", async () => {
    await page.evaluate(() => {
      const setVal = (testId, val) => {
        const el = document.querySelector(`[data-testid="${testId}"]`);
        if (!el) throw new Error(testId);
        const proto = window.HTMLInputElement.prototype;
        const desc = Object.getOwnPropertyDescriptor(proto, "value");
        desc.set.call(el, val);
        el.dispatchEvent(new Event("input", { bubbles: true }));
      };
      setVal("intake-v6-acm-field-l1_mm", "83");
      setVal("intake-v6-acm-field-l2_mm", "28");
    });
    await page.waitForTimeout(100);
    await page.getByTestId("intake-v6-product-component-row-letters").click();
  });

  await page.screenshot({ path: path.join(OUT, "shots", "02-after.png") });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.getByTestId("intake-v6-header").waitFor({ state: "visible", timeout: 90000 });
  const afterRefresh = await getL1();
  await page.screenshot({ path: path.join(OUT, "shots", "03-refresh.png") });

  const confirmCase = cases.find((c) => c.name === "confirm_with_pending_82");
  const typingCase = cases.find((c) => c.name === "typing_65");
  const twoFields = cases.find((c) => c.name === "two_fields_flush");
  const report = {
    workspace: "IV6-DB2F86B7",
    cases,
    afterRefreshL1: afterRefresh,
    pass:
      (typingCase?.requestCount ?? 99) === 1 &&
      (confirmCase?.requestCount ?? 99) === 1 &&
      (confirmCase?.puts?.[0]?.authL1 === "operator_confirmed") &&
      cases
        .filter((c) => c.name !== "two_fields_flush")
        .every((c) => c.requestCount <= 1) &&
      // two fields: prefer 1 combined; allow ≤2 (one per field) per owner note
      (twoFields?.requestCount ?? 99) <= 2,
  };
  fs.writeFileSync(path.join(OUT, "network-proof.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
  if (!report.pass) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
