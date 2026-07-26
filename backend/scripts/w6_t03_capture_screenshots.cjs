const { chromium } = require("playwright");
const path = require("node:path");

const outDir = path.resolve(
  __dirname,
  "../../docs/qa/product-system-active-path-isolation-v1/w6_t03_screenshots",
);

const shots = [
  {
    file: "01_execution_detail_blocked_strip.png",
    url: "http://127.0.0.1:3000/execution/23150",
    prep: async (page) => {
      await page.getByRole("button", { name: "Detalii decizii" }).click();
      await page.waitForTimeout(500);
    },
  },
  {
    file: "03_blocking_decisions_details.png",
    url: "http://127.0.0.1:3000/execution/23150",
    prep: async (page) => {
      await page.getByRole("button", { name: "Detalii decizii" }).click();
      await page.waitForTimeout(500);
      await page.getByText("Blocante productie").scrollIntoViewIfNeeded();
    },
  },
  {
    file: "04_nonblocking_internal_analysis.png",
    url: "http://127.0.0.1:3000/execution/23150",
    prep: async (page) => {
      await page.getByRole("button", { name: "Detalii decizii" }).click();
      await page.waitForTimeout(500);
      await page.getByText("Analiza interna (nu blocheaza productia)").scrollIntoViewIfNeeded();
    },
  },
  {
    file: "05_task_row_production_block_identity.png",
    url: "http://127.0.0.1:3000/execution/23150",
    prep: async (page) => {
      await page.getByText("Blocat pentru productie").first().scrollIntoViewIfNeeded();
    },
  },
  {
    file: "08_manager_metadata_admin.png",
    url: "http://127.0.0.1:3000/execution/23150",
    prep: async (page) => {
      await page.getByRole("button", { name: "Detalii decizii" }).click();
      await page.waitForTimeout(500);
      await page.getByText("Poate rezolva: da").first().scrollIntoViewIfNeeded();
    },
  },
  {
    file: "07_allowed_release_comparison_23099.png",
    url: "http://127.0.0.1:3000/execution/23099",
  },
  {
    file: "06_operator_view_blocked_release.png",
    url: "http://127.0.0.1:3000/operator?orderId=23150",
    prep: async (page) => {
      await page.waitForSelector('[data-testid="operator-production-release-status"]', {
        timeout: 15000,
      });
    },
  },
  {
    file: "09_refresh_stability_blocked.png",
    url: "http://127.0.0.1:3000/execution/23150",
    prep: async (page) => {
      await page.getByRole("button", { name: "Refresh" }).click();
      await page.waitForTimeout(800);
      await page.getByRole("button", { name: "Refresh" }).click();
      await page.waitForTimeout(800);
    },
  },
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  for (const shot of shots) {
    await page.goto(shot.url, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    if (shot.prep) await shot.prep(page);
    await page.screenshot({ path: path.join(outDir, shot.file), fullPage: true });
    console.log("saved", shot.file);
  }
  await browser.close();
})();
