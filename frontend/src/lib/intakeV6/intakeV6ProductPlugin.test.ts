import { describe, expect, it } from "vitest";
import {
  listIntakeV6ProductPlugins,
  resolveIntakeV6ProductPlugin,
  resolveIntakeV6ReviewTabs,
} from "./intakeV6ProductPlugin";

describe("intakeV6ProductPlugin", () => {
  it("resolves volumetric letters by canonical and alias template codes", () => {
    const byV2 = resolveIntakeV6ProductPlugin("TPL-VOLUMETRIC-LETTERS_v2");
    const byLegacy = resolveIntakeV6ProductPlugin("TPL-VOLUMETRIC-LETTERS");
    expect(byV2).not.toBeNull();
    expect(byLegacy).toBe(byV2);
    expect(byV2?.displayName).toBe("Litere volumetrice");
  });

  it("normalizes template code casing and whitespace", () => {
    const plugin = resolveIntakeV6ProductPlugin("  tpl-volumetric-letters  ");
    expect(plugin?.templateCode).toBe("TPL-VOLUMETRIC-LETTERS_v2");
  });

  it("returns null for unknown templates", () => {
    expect(resolveIntakeV6ProductPlugin("TPL-UNKNOWN")).toBeNull();
    expect(resolveIntakeV6ProductPlugin(null)).toBeNull();
    expect(resolveIntakeV6ProductPlugin("")).toBeNull();
  });

  it("returns review tabs from plugin with module code links", () => {
    const tabs = resolveIntakeV6ReviewTabs("TPL-VOLUMETRIC-LETTERS_v2");
    expect(tabs.map((t) => t.id)).toEqual(["finisaje", "iluminare", "montaj"]);
    expect(tabs[0]?.moduleCodes).toContain("face");
    expect(tabs[1]?.moduleCodes).toContain("led");
    expect(tabs[2]?.moduleCodes).toContain("mounting");
  });

  it("falls back to volumetric review tabs when template is unknown", () => {
    const tabs = resolveIntakeV6ReviewTabs("TPL-UNKNOWN");
    expect(tabs).toHaveLength(3);
    expect(tabs[0]?.id).toBe("finisaje");
  });

  it("lists registered plugins", () => {
    expect(listIntakeV6ProductPlugins()).toHaveLength(1);
  });
});
