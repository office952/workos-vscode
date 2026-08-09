/**
 * Playwright capture for MachineRun UI CREATE/ADD/context links.
 * Targets isolated :3010 (BACKEND_PORT=8010). Never QA writes.
 */
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(process.cwd(), "package.json"));
const { chromium } = require("playwright");
const OUT = path.join(__dirname, "screenshots");
const BASE = process.env.MR_UI_BASE || "http://127.0.0.1:3010";
fs.mkdirSync(OUT, { recursive: true });

async function setTheme(page, theme) {
  await page.evaluate((t) => {
    document.documentElement.classList.toggle("dark", t === "dark");
    localStorage.setItem("theme", t);
  }, theme);
  await page.waitForTimeout(200);
}

async function shot(page, name) {
  const file = path.join(OUT, name);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();
  const network = [];
  const consoleErrs = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrs.push(msg.text());
  });
  page.on("pageerror", (err) => consoleErrs.push(String(err)));
  page.on("response", async (res) => {
    const url = res.url();
    if (!url.includes("/machine-runs")) return;
    network.push({
      method: res.request().method(),
      url,
      status: res.status(),
    });
  });

  const report = {
    base: BASE,
    screenshots: [],
    network: [],
    consoleErrors: [],
    requestVolume: {},
  };

  // --- List + CREATE ---
  await page.goto(`${BASE}/execution/machine-runs`, { waitUntil: "networkidle" });
  await setTheme(page, "light");
  report.screenshots.push(await shot(page, "mr_list_create_ready_light.png"));
  await page.getByTestId("machine-runs-create-open").click();
  await page.getByTestId("machine-run-create-dialog").waitFor();
  report.screenshots.push(await shot(page, "mr_create_dialog_light.png"));
  await page.getByTestId("machine-run-create-machine").selectOption({ index: 1 });
  await page.waitForTimeout(800);
  report.screenshots.push(await shot(page, "mr_create_candidates_light.png"));

  // select first two checkboxes
  const boxes = page.locator('[data-testid^="machine-run-create-candidate-"] input[type="checkbox"]');
  const boxCount = await boxes.count();
  if (boxCount >= 2) {
    await boxes.nth(0).check();
    await boxes.nth(1).check();
  }
  report.screenshots.push(await shot(page, "mr_create_selected_light.png"));
  await page.getByTestId("machine-run-create-submit").click();
  await page.waitForURL(/\/execution\/machine-runs\/\d+/, { timeout: 15000 });
  await page.waitForTimeout(500);
  report.screenshots.push(await shot(page, "mr_create_detail_after_light.png"));

  // dark CREATE reopen
  await page.goto(`${BASE}/execution/machine-runs`, { waitUntil: "networkidle" });
  await setTheme(page, "dark");
  await page.getByTestId("machine-runs-create-open").click();
  await page.getByTestId("machine-run-create-dialog").waitFor();
  await page.getByTestId("machine-run-create-machine").selectOption({ index: 1 });
  await page.waitForTimeout(600);
  report.screenshots.push(await shot(page, "mr_create_dialog_dark.png"));
  await page.keyboard.press("Escape");

  // --- ADD on HELD ---
  const heldId = JSON.parse(
    fs.readFileSync(path.join(__dirname, "_isolated_closure_ids.json"), "utf8"),
  ).ids.HELD;
  await page.goto(`${BASE}/execution/machine-runs/${heldId}`, { waitUntil: "networkidle" });
  await setTheme(page, "light");
  await page.getByTestId("machine-run-add-open").click();
  await page.getByTestId("machine-run-add-picker").waitFor();
  report.screenshots.push(await shot(page, "mr_add_picker_light.png"));
  const addRadio = page.locator('[data-testid^="machine-run-add-candidate-"] input[type="radio"]').first();
  if (await addRadio.count()) {
    await addRadio.check();
    await page.getByTestId("machine-run-add-submit").click();
    await page.waitForTimeout(800);
  }
  report.screenshots.push(await shot(page, "mr_add_after_light.png"));

  await setTheme(page, "dark");
  await page.getByTestId("machine-run-add-open").click();
  await page.waitForTimeout(500);
  report.screenshots.push(await shot(page, "mr_add_picker_dark.png"));

  // --- Ops-Graph chip (RUNNING plan / order 880755) ---
  await page.goto(`${BASE}/execution/ops-graph?orderId=880755`, {
    waitUntil: "networkidle",
  });
  await setTheme(page, "light");
  await page.waitForTimeout(1200);
  const taskList = page.getByTestId("ops-graph-task-list");
  if (await taskList.count()) {
    report.requestVolume.opsGraph = {
      taskCount: await taskList.getAttribute("data-machine-run-task-count"),
      lookupCount: await taskList.getAttribute("data-machine-run-lookup-count"),
    };
  }
  report.screenshots.push(await shot(page, "ops_graph_chip_light.png"));
  await setTheme(page, "dark");
  report.screenshots.push(await shot(page, "ops_graph_chip_dark.png"));

  // --- Execution detail chip (same order) ---
  await page.goto(`${BASE}/execution/880755`, { waitUntil: "networkidle" });
  await setTheme(page, "light");
  await page.waitForTimeout(1200);
  const work = page.getByTestId("execution-work-panel-machine-run-lookups");
  if (await work.count()) {
    report.requestVolume.executionDetail = {
      taskCount: await work.getAttribute("data-task-count"),
      lookupCount: await work.getAttribute("data-lookup-count"),
    };
  }
  report.screenshots.push(await shot(page, "execution_detail_chip_light.png"));
  await setTheme(page, "dark");
  report.screenshots.push(await shot(page, "execution_detail_chip_dark.png"));

  // regression smoke
  for (const route of ["/shop-floor", "/utilaje", "/modules", "/governance"]) {
    await page.goto(`${BASE}${route}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(400);
  }

  report.network = network;
  report.consoleErrors = consoleErrs;
  fs.writeFileSync(
    path.join(__dirname, "browser_capture_report.json"),
    JSON.stringify(report, null, 2),
  );
  fs.writeFileSync(
    path.join(__dirname, "console_proof.json"),
    JSON.stringify(
      { base: BASE, consoleErrors: consoleErrs, ok: consoleErrs.length === 0 },
      null,
      2,
    ),
  );
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
