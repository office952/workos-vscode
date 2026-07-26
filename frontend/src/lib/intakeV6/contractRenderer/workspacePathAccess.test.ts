import { describe, expect, it } from "vitest";
import {
  getByWorkspacePath,
  isPathAllowlisted,
  setByWorkspacePath,
} from "./workspacePathAccess";

const allowlist = [
  "finish_setup.lighting_system_type",
  "finish_setup.mounting_template_enabled",
  "finish_setup.mounting_template_area_m2",
];

describe("workspacePathAccess", () => {
  it("reads nested values and reports missing", () => {
    const root = { finish_setup: { lighting_system_type: "led_modules" } };
    expect(getByWorkspacePath(root, "finish_setup.lighting_system_type")).toEqual({
      ok: true,
      value: "led_modules",
      missing: false,
    });
    expect(getByWorkspacePath(root, "finish_setup.missing_key")).toEqual({
      ok: true,
      value: undefined,
      missing: true,
    });
  });

  it("writes only allowlisted paths and preserves siblings", () => {
    const root = {
      finish_setup: {
        lighting_system_type: "led_modules",
        mounting_template_enabled: false,
      },
    };
    const denied = setByWorkspacePath(root, "finish_setup.secret", true, allowlist);
    expect(denied.ok).toBe(false);

    const written = setByWorkspacePath(
      root,
      "finish_setup.mounting_template_enabled",
      true,
      allowlist,
    );
    expect(written.ok).toBe(true);
    if (!written.ok) return;
    expect(written.next.finish_setup).toMatchObject({
      lighting_system_type: "led_modules",
      mounting_template_enabled: true,
    });
    expect(root.finish_setup.mounting_template_enabled).toBe(false);
  });

  it("checks allowlist exactly", () => {
    expect(isPathAllowlisted("finish_setup.lighting_system_type", allowlist)).toBe(true);
    expect(isPathAllowlisted("finish_setup", allowlist)).toBe(false);
  });
});
