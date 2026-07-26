const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/app_int_01_screenshots",
);
const BASE = "http://127.0.0.1:3000";
const VIEWPORT = { width: 1440, height: 900 };

const ROUTES = [
  { file: "01_employees.png", url: "/employees", wait: 4000 },
  { file: "02_employees_records.png", url: "/employees-records", wait: 3000 },
  { file: "03_attendance.png", url: "/attendance", wait: 3000 },
  { file: "04_utilaje.png", url: "/utilaje", wait: 4000 },
  { file: "05_shop_floor.png", url: "/shop-floor", wait: 4000 },
  { file: "06_operator.png", url: "/operator", wait: 4000 },
  { file: "07_tablet.png", url: "/tablet", wait: 3000 },
  { file: "08_employee_mobile_v2.png", url: "/employee-app-v2/tasks", wait: 4000, mobile: true },
];

fs.mkdirSync(outDir, { recursive: true });

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();
  let ok = 0;
  for (const route of ROUTES) {
    try {
      if (route.mobile) {
        await page.setViewportSize({ width: 390, height: 844 });
      } else {
        await page.setViewportSize(VIEWPORT);
      }
      await page.goto(`${BASE}${route.url}`, { waitUntil: "networkidle", timeout: 60000 });
      await page.waitForTimeout(route.wait);
      await page.screenshot({ path: path.join(outDir, route.file), fullPage: true });
      console.log("ok", route.file, route.url);
      ok += 1;
    } catch (err) {
      console.error("fail", route.file, err.message);
    }
  }
  await browser.close();
  console.log(`captured ${ok}/${ROUTES.length} -> ${outDir}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
