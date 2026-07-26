import fs from "fs";
import path from "path";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(__dirname, "../../../frontend/package.json"));
const { chromium } = require("playwright");

const UI = "http://127.0.0.1:3000";
const id = "3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982";
const shots = path.join(__dirname, "screenshots");

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await page.goto(`${UI}/intake-v6/${id}/operator`, { waitUntil: "networkidle", timeout: 60000 });
await page.waitForTimeout(1200);
await page.locator('[data-testid="intake-v6-review-tab-montaj"]').click();
await page.waitForTimeout(1000);

const probe = await page.evaluate(() => {
  const active = document.querySelector(
    '[data-testid="intake-v6-review-tab-montaj"][aria-selected="true"]',
  );
  const text = document.body.innerText || "";
  return {
    montajSelected: !!active,
    hasFundal: /Fundal/i.test(text),
    hasProductSystem: /Product System/i.test(text),
    hasTarife: /Tarife lips/i.test(text),
    hasAccesorii: /Accesorii montaj/i.test(text),
    hasScope: /Fără pregătire|Doar pregătire|montaj la locație/i.test(text),
    hasSegmented: /segment|panouri|îmbin/i.test(text),
    snippet: text
      .split("\n")
      .map((l) => l.trim())
      .filter((l) =>
        /Montaj|Fundal|pregătire|șablon|sablon|Product System|Tarife|Accesorii|segment|panou|carcas/i.test(
          l,
        ),
      )
      .slice(0, 50),
  };
});
console.log(JSON.stringify(probe, null, 2));
await page.screenshot({ path: path.join(shots, "10_montaj_tab_selected_1440.png") });

const details = page.getByRole("button", { name: /Detalii linii/i }).first();
if (await details.count()) {
  await details.click({ force: true });
  await page.waitForTimeout(900);
  await page.screenshot({ path: path.join(shots, "12_pricing_details_lines.png") });
}

await page.getByRole("button", { name: /Continuă la Confirmare/i }).click({ force: true }).catch(() => {});
await page.waitForTimeout(1800);
await page.screenshot({ path: path.join(shots, "13_confirmare_page.png") });
const conf = { url: page.url(), title: await page.title() };
console.log("confirm", conf);

fs.writeFileSync(
  path.join(__dirname, "runtime/montaj_tab_probe.json"),
  JSON.stringify({ probe, conf }, null, 2),
);
await browser.close();
