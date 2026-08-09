/**
 * Browser capture for controlled validation — isolated FE→BE only.
 * Evidence type: BROWSER_RUNTIME_EVIDENCE
 */
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const feRoot = path.resolve(__dirname, "../../../frontend");
const require = createRequire(path.join(feRoot, "package.json"));
const { chromium } = require("playwright");

const FE = process.env.FE_BASE || "http://127.0.0.1:3013";
const OUT = path.join(__dirname, "screenshots");
const REPORT = path.join(__dirname, "browser_capture_report.json");
fs.mkdirSync(OUT, { recursive: true });

const consoleErrors = [];
const pageErrors = [];

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, name), fullPage: true });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => pageErrors.push(String(err)));

  const report = {
    fe: FE,
    evidence_type: "BROWSER_RUNTIME_EVIDENCE",
    themes: {},
    refresh: {},
  };

  for (const theme of ["light", "dark"]) {
    await page.addInitScript((t) => {
      localStorage.setItem("vite-ui-theme", t);
      localStorage.setItem("theme", t);
      document.documentElement.classList.toggle("dark", t === "dark");
    }, theme);
    await page.goto(`${FE}/execution/machine-runs`, {
      waitUntil: "networkidle",
      timeout: 45000,
    });
    await page.waitForTimeout(900);
    const body = await page.evaluate(() => document.body.innerText);
    await shot(page, `list_${theme}.png`);
    const hasCreate = await page
      .getByRole("button", { name: /Rulare utilaj|Crează/i })
      .count()
      .then((c) => c > 0);
    report.themes[theme] = {
      list_ok: body.length > 50,
      has_create_affordance: hasCreate,
      deferred_stale: /Crearea rulărilor este amânată|Adăugarea este amânată/i.test(
        body
      ),
      pause_controls: /\bPAUSE\b|\bRESUME\b/.test(body),
    };

    const link = page.locator('a[href*="/execution/machine-runs/"]').first();
    if (await link.count()) {
      await link.click();
      await page.waitForTimeout(800);
      await shot(page, `detail_${theme}.png`);
      const detailText = await page.evaluate(() => document.body.innerText);
      report.themes[theme].detail_ok = detailText.length > 50;
      report.themes[theme].release_hint =
        /eliber|RELEASE|Eliberează|rezervat/i.test(detailText);
    }
  }

  await page.goto(`${FE}/execution/machine-runs`, {
    waitUntil: "networkidle",
    timeout: 45000,
  });
  const before = await page.evaluate(() => document.body.innerText.slice(0, 200));
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(600);
  const after = await page.evaluate(() => document.body.innerText.slice(0, 200));
  report.refresh = {
    reconstructed: after.length > 50,
    roughly_stable: /Rulare|utilaj|machine/i.test(after),
    before_sample: before.slice(0, 80),
    after_sample: after.slice(0, 80),
  };
  report.console_errors_filtered = consoleErrors.filter(
    (e) => !/favicon|React Router Future Flag/i.test(e)
  );
  report.page_errors_filtered = pageErrors;

  fs.writeFileSync(REPORT, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
