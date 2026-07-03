import { defineConfig } from "@playwright/test";

const baseURL = process.env.PW_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  retries: 0,
  use: {
    baseURL,
    headless: true,
    trace: "off",
  },
  webServer: process.env.PW_SKIP_WEB_SERVER
    ? undefined
    : {
        command: "npm run dev",
        url: baseURL,
        reuseExistingServer: true,
        timeout: 120_000,
      },
});
