import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.DEMO_FE_BASE || "http://127.0.0.1:3010";
const OUT = path.resolve(__dirname, "screenshots");
fs.mkdirSync(OUT, { recursive: true });

const routes = [
  ["01-dashboard", "/dashboard"],
  ["02-intake", "/intake"],
  ["03-intake-v6-letters", "/intake-v6/d0e10001-0000-4000-8000-000000000001/operator"],
  ["04-intake-v6-draft", "/intake-v6/d0e10002-0000-4000-8000-000000000002/operator"],
  ["05-product-system-products", "/product-system/products"],
  ["06-inventory-pricing", "/inventory/pricing"],
  ["07-quotes", "/quotes"],
  ["08-quotes-1", "/quotes/1"],
  ["09-orders", "/orders"],
  ["10-orders-1", "/orders/1"],
  ["11-execution", "/execution"],
  ["12-execution-1", "/execution/1"],
  ["13-machine-runs", "/execution/machine-runs"],
  ["14-modules", "/modules"],
  ["15-governance", "/governance"],
];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const results = [];

for (const [name, route] of routes) {
  const url = BASE + route;
  try {
    const resp = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(1500);
    const body = await page.evaluate(() => (document.body && document.body.innerText) || "");
    const file = path.join(OUT, `${name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    const hasDemo =
      /DEMO-|Demo Client|Demo Operator|862[,.]65|DEMO-QUOTE|DEMO-ORDER|DEMO-INTAKE/i.test(
        body,
      );
    results.push({
      name,
      route,
      http: resp ? resp.status() : null,
      bodyLen: body.length,
      demoSignal: hasDemo,
      screenshot: path.basename(file),
    });
    console.log(name, resp && resp.status(), `demoSignal=${hasDemo}`, `bodyLen=${body.length}`);
  } catch (e) {
    const err = String(e && e.message ? e.message : e);
    results.push({ name, route, status: "FAIL", err });
    console.log(name, "FAIL", err);
  }
}

const outJson = path.resolve(__dirname, "route_smoke.json");
fs.writeFileSync(outJson, JSON.stringify({ base: BASE, results }, null, 2) + "\n");
console.log("wrote", outJson);
await browser.close();
const fails = results.filter((r) => r.status === "FAIL" || (r.http && r.http >= 400));
process.exit(fails.length ? 1 : 0);
