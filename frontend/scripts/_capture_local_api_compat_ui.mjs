import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../../docs/qa/local-api-truth-stale-backend-2026-07-19");
const shots = path.join(OUT, "screenshots");
const runtime = path.join(OUT, "runtime");
fs.mkdirSync(shots, { recursive: true });
fs.mkdirSync(runtime, { recursive: true });

const label = process.argv[2] || "shot";
const url = process.argv[3] || "http://127.0.0.1:3000/";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90_000 });
await page.waitForTimeout(3000);
const shotPath = path.join(shots, `${label}.png`);
await page.screenshot({ path: shotPath, fullPage: true });
const banner = await page.locator('[data-testid="local-api-compat-banner"]').count();
const title = await page
  .locator('[data-testid="local-api-compat-title"]')
  .textContent()
  .catch(() => null);
const apiBase = await page
  .locator('[data-testid="local-api-compat-api-base"]')
  .textContent()
  .catch(() => null);
const writeErr = await page.evaluate(async () => {
  try {
    await fetch("http://127.0.0.1:8001/api/v1/intake-v6/workspaces/x/finish-setup", {
      method: "PUT",
      body: "{}",
    });
    return "WRITE_ALLOWED";
  } catch (e) {
    return String(e && e.message ? e.message : e);
  }
});
const payload = { label, url, banner, title, apiBase, writeErr, shotPath };
fs.writeFileSync(path.join(runtime, `${label}.json`), JSON.stringify(payload, null, 2));
console.log(JSON.stringify(payload, null, 2));
await browser.close();
