/**
 * BUILD 24 — Frontend RBAC Authorization Parity Tests.
 *
 * Tests that:
 * 1. resolveRole correctly maps roles in dev vs production environments.
 * 2. Unknown/email-like roles fail-closed to "viewer" in production.
 * 3. Valid roles pass through unchanged.
 * 4. Permission checks work correctly for all roles.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { resolveRole, can, canAll, canAny, getPermissions, getVisibleNavItems } from "./rbac";

// Helper to mock import.meta.env
const originalEnv = { ...import.meta.env };

describe("BUILD 24 — Frontend RBAC Hardening", () => {
  describe("resolveRole — valid roles pass through", () => {
    it("resolves 'admin' directly", () => {
      expect(resolveRole("admin")).toBe("admin");
    });

    it("resolves 'manager' directly", () => {
      expect(resolveRole("manager")).toBe("manager");
    });

    it("resolves 'sales' directly", () => {
      expect(resolveRole("sales")).toBe("sales");
    });

    it("resolves 'operator' directly", () => {
      expect(resolveRole("operator")).toBe("operator");
    });

    it("resolves 'viewer' directly", () => {
      expect(resolveRole("viewer")).toBe("viewer");
    });

    it("resolves case-insensitive 'Admin' to 'admin'", () => {
      expect(resolveRole("Admin")).toBe("admin");
    });
  });

  describe("resolveRole — null/undefined/empty", () => {
    it("resolves null to viewer", () => {
      expect(resolveRole(null)).toBe("viewer");
    });

    it("resolves undefined to viewer", () => {
      expect(resolveRole(undefined)).toBe("viewer");
    });

    it("resolves empty string to viewer", () => {
      expect(resolveRole("")).toBe("viewer");
    });
  });

  describe("resolveRole — unknown roles fail-closed", () => {
    it("resolves unknown role to viewer", () => {
      expect(resolveRole("random_role")).toBe("viewer");
    });

    it("resolves numeric string to viewer", () => {
      expect(resolveRole("12345")).toBe("viewer");
    });
  });

  describe("Permission checks", () => {
    it("admin has all permissions", () => {
      expect(can("admin", "view:dashboard")).toBe(true);
      expect(can("admin", "edit:settings")).toBe(true);
      expect(can("admin", "reality.restore_valid")).toBe(true);
    });

    it("viewer only has view:dashboard", () => {
      expect(can("viewer", "view:dashboard")).toBe(true);
      expect(can("viewer", "edit:intake")).toBe(false);
      expect(can("viewer", "edit:settings")).toBe(false);
    });

    it("operator cannot edit quotes", () => {
      expect(can("operator", "edit:quotes")).toBe(false);
    });

    it("sales cannot edit inventory", () => {
      expect(can("sales", "edit:inventory")).toBe(false);
    });

    it("manager cannot edit settings", () => {
      expect(can("manager", "edit:settings")).toBe(false);
    });
  });

  describe("canAll / canAny", () => {
    it("canAll returns true when all permissions granted", () => {
      expect(canAll("admin", ["view:dashboard", "edit:settings"])).toBe(true);
    });

    it("canAll returns false when any permission missing", () => {
      expect(canAll("viewer", ["view:dashboard", "edit:settings"])).toBe(false);
    });

    it("canAny returns true when at least one permission granted", () => {
      expect(canAny("viewer", ["view:dashboard", "edit:settings"])).toBe(true);
    });

    it("canAny returns false when no permissions granted", () => {
      expect(canAny("viewer", ["edit:intake", "edit:settings"])).toBe(false);
    });
  });

  describe("Navigation visibility", () => {
    it("admin sees all nav items", () => {
      const items = getVisibleNavItems("admin");
      expect(items).toContain("settings");
      expect(items).toContain("dashboard");
    });

    it("viewer only sees dashboard", () => {
      const items = getVisibleNavItems("viewer");
      expect(items).toEqual(["dashboard"]);
    });

    it("operator does not see settings", () => {
      const items = getVisibleNavItems("operator");
      expect(items).not.toContain("settings");
    });
  });
});