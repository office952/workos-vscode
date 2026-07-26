import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.resetModules();
  vi.unstubAllEnvs();
});

describe("getAPIBaseURL resolution order", () => {
  it("honors explicit VITE_API_BASE_URL in DEV", async () => {
    vi.stubEnv("DEV", true);
    vi.stubEnv("VITE_API_BASE_URL", "http://127.0.0.1:8002/");
    const { getAPIBaseURL, loadRuntimeConfig } = await import("./config");
    await loadRuntimeConfig();
    expect(getAPIBaseURL()).toBe("http://127.0.0.1:8002");
  });

  it("uses same-origin fallback in DEV when VITE_API_BASE_URL is absent", async () => {
    vi.stubEnv("DEV", true);
    vi.stubEnv("VITE_API_BASE_URL", "");
    const { getAPIBaseURL, loadRuntimeConfig } = await import("./config");
    await loadRuntimeConfig();
    expect(getAPIBaseURL()).toBe("");
  });

  it("does not use localhost fallback outside DEV", async () => {
    vi.stubEnv("DEV", false);
    vi.stubEnv("VITE_API_BASE_URL", "");
    const { getAPIBaseURL, loadRuntimeConfig } = await import("./config");
    await loadRuntimeConfig();
    expect(getAPIBaseURL()).toBe("");
  });
});
