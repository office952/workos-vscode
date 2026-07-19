import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  __resetLocalApiCompatibilityForTests,
  evaluateLocalCompatibilityPayload,
  installLocalApiWriteGuard,
  isLocalApiWriteBlocked,
  LOCAL_COMPAT_CONTRACT,
  LOCAL_COMPAT_REQUIRED_CAPABILITIES,
  probeLocalApiCompatibility,
  resolveCompatProbeUrl,
} from "./localApiCompatibility";

const originalFetch = globalThis.fetch;

beforeEach(() => {
  __resetLocalApiCompatibilityForTests();
});

afterEach(() => {
  __resetLocalApiCompatibilityForTests();
  globalThis.fetch = originalFetch;
  const g = globalThis as typeof globalThis & { __workosLocalApiWriteGuardPatched?: boolean };
  delete g.__workosLocalApiWriteGuardPatched;
  vi.unstubAllEnvs();
});

describe("localApiCompatibility", () => {
  it("builds probe URL from explicit API base and same-origin", () => {
    expect(resolveCompatProbeUrl("http://127.0.0.1:8002")).toBe(
      "http://127.0.0.1:8002/api/v1/system/local-compatibility",
    );
    expect(resolveCompatProbeUrl("")).toBe("/api/v1/system/local-compatibility");
  });

  it("marks missing endpoint as incompatible (stale schema)", () => {
    const snap = evaluateLocalCompatibilityPayload("http://127.0.0.1:8001", 404, null);
    expect(snap.kind).toBe("incompatible");
    expect(snap.missingCapabilities).toEqual([...LOCAL_COMPAT_REQUIRED_CAPABILITIES]);
  });

  it("rejects non-WorkOS service payloads", () => {
    const snap = evaluateLocalCompatibilityPayload("http://example.test", 200, {
      service: "other",
      contract: LOCAL_COMPAT_CONTRACT,
      capabilities: [...LOCAL_COMPAT_REQUIRED_CAPABILITIES],
    });
    expect(snap.kind).toBe("incompatible");
  });

  it("passes when contract and capabilities match", () => {
    const snap = evaluateLocalCompatibilityPayload("http://127.0.0.1:8002", 200, {
      service: "workos-backend",
      contract: LOCAL_COMPAT_CONTRACT,
      api_version: "BUILD_25",
      capabilities: [...LOCAL_COMPAT_REQUIRED_CAPABILITIES],
    });
    expect(snap.kind).toBe("ok");
    expect(snap.apiVersion).toBe("BUILD_25");
  });

  it("probe marks unavailable on network failure", async () => {
    vi.stubEnv("DEV", true);
    const snap = await probeLocalApiCompatibility({
      apiBase: "http://127.0.0.1:59999",
      fetchImpl: async () => {
        throw new TypeError("Failed to fetch");
      },
    });
    expect(snap.kind).toBe("unavailable");
    expect(isLocalApiWriteBlocked()).toBe(true);
  });

  it("write guard blocks mutating API calls when incompatible", async () => {
    vi.stubEnv("DEV", true);
    __resetLocalApiCompatibilityForTests(
      evaluateLocalCompatibilityPayload("http://127.0.0.1:8001", 404, null),
    );
    installLocalApiWriteGuard();
    await expect(
      fetch("http://127.0.0.1:8001/api/v1/intake-v6/workspaces/x/finish-setup", {
        method: "PUT",
        body: "{}",
      }),
    ).rejects.toThrow(/Scriere blocata/i);
  });
});
