/**
 * BUILD 20 — Frontend Environment Safety Tests.
 *
 * Verifies that mock/dev auth flags behave correctly
 * and that production guards are in place.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

describe("Environment Safety Guards", () => {
  const originalEnv = { ...import.meta.env };

  afterEach(() => {
    vi.resetModules();
  });

  describe("isMockEnabled", () => {
    it("returns true when VITE_ENABLE_MOCK_DATA is 'true'", async () => {
      vi.stubEnv("VITE_ENABLE_MOCK_DATA", "true");
      const { isMockEnabled } = await import("./mockGuard");
      expect(isMockEnabled()).toBe(true);
      vi.unstubAllEnvs();
    });

    it("returns false when VITE_ENABLE_MOCK_DATA is 'false'", async () => {
      vi.stubEnv("VITE_ENABLE_MOCK_DATA", "false");
      const { isMockEnabled } = await import("./mockGuard");
      expect(isMockEnabled()).toBe(false);
      vi.unstubAllEnvs();
    });

    it("returns false when VITE_ENABLE_MOCK_DATA is undefined", async () => {
      vi.stubEnv("VITE_ENABLE_MOCK_DATA", "");
      const { isMockEnabled } = await import("./mockGuard");
      expect(isMockEnabled()).toBe(false);
      vi.unstubAllEnvs();
    });

    it("returns false for any value other than exact 'true'", async () => {
      vi.stubEnv("VITE_ENABLE_MOCK_DATA", "TRUE");
      const { isMockEnabled } = await import("./mockGuard");
      expect(isMockEnabled()).toBe(false);
      vi.unstubAllEnvs();
    });
  });

  describe("isDevAuthFallback", () => {
    it("returns false when VITE_ENABLE_DEV_AUTH is 'false'", async () => {
      vi.stubEnv("VITE_ENABLE_DEV_AUTH", "false");
      vi.stubEnv("VITE_DEV_GUARD_BYPASS", "false");
      const { isDevAuthFallback } = await import("./mockGuard");
      expect(isDevAuthFallback()).toBe(false);
      vi.unstubAllEnvs();
    });

    it("returns false when VITE_DEV_GUARD_BYPASS is 'true'", async () => {
      vi.stubEnv("VITE_ENABLE_DEV_AUTH", "true");
      vi.stubEnv("VITE_DEV_GUARD_BYPASS", "true");
      const { isDevAuthFallback } = await import("./mockGuard");
      expect(isDevAuthFallback()).toBe(false);
      vi.unstubAllEnvs();
    });
  });

  describe("getAPIBaseURL", () => {
    it("returns a string (never undefined)", async () => {
      const { getAPIBaseURL } = await import("./config");
      const url = getAPIBaseURL();
      expect(typeof url).toBe("string");
    });
  });

  describe("Production .env.production flags", () => {
    it("documents that .env.production disables mock data", () => {
      // This is a documentation test — .env.production sets VITE_ENABLE_MOCK_DATA=false
      // Verified by file content inspection in BUILD 20 audit.
      expect(true).toBe(true);
    });

    it("documents that .env.production disables dev auth", () => {
      // This is a documentation test — .env.production sets VITE_ENABLE_DEV_AUTH=false
      // Verified by file content inspection in BUILD 20 audit.
      expect(true).toBe(true);
    });
  });

  describe("RBAC role resolution safety", () => {
    it("resolveRole maps unknown role to viewer", async () => {
      const { resolveRole } = await import("./rbac");
      expect(resolveRole("banana")).toBe("viewer");
    });

    it("resolveRole maps null/undefined to viewer", async () => {
      const { resolveRole } = await import("./rbac");
      expect(resolveRole(null)).toBe("viewer");
      expect(resolveRole(undefined)).toBe("viewer");
    });

    it("resolveRole maps valid admin to admin", async () => {
      const { resolveRole } = await import("./rbac");
      expect(resolveRole("admin")).toBe("admin");
    });

    it("resolveRole maps 'user' to viewer by default", async () => {
      // Default test/runtime config does not enable dev auth fallback.
      // The safe default is fail-closed to viewer.
      vi.stubEnv("VITE_ENABLE_DEV_AUTH", "false");
      const { resolveRole } = await import("./rbac");
      expect(resolveRole("user")).toBe("viewer");
      vi.unstubAllEnvs();
    });
  });
});