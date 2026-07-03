import { describe, expect, it } from "vitest";
import {
  ALL_COLOR_REGISTRY_ITEMS,
  filterColorRegistry,
  findColorRegistryItem,
  formatColorRegistryLabel,
  lookupColorRegistryItem,
  normalizeColorRegistryCode,
  searchColorRegistry,
} from "./colorRegistry";

describe("colorRegistry", () => {
  it("finds RAL items by code", () => {
    const item = findColorRegistryItem("RAL", "9010");
    expect(item).toBeDefined();
    expect(item?.system).toBe("RAL");
    expect(formatColorRegistryLabel(item!)).toContain("9010");
  });

  it("normalizes RAL and Oracal code prefixes", () => {
    expect(normalizeColorRegistryCode("RAL", " RAL 7016 ")).toBe("7016");
    expect(normalizeColorRegistryCode("ORACAL", "651-010", "651")).toBe("010");
    expect(normalizeColorRegistryCode("ORACAL", "Oracal 8500-010", "8500")).toBe("010");
  });

  it("finds items after code normalization", () => {
    const item = findColorRegistryItem("RAL", "RAL 9010");
    expect(item?.code).toBe("9010");
  });

  it("returns unknown lookup result for missing codes", () => {
    const result = lookupColorRegistryItem("RAL", "RAL 9999");
    expect(result.status).toBe("unknown");
    if (result.status === "unknown") {
      expect(result.normalizedCode).toBe("9999");
    }
  });

  it("finds Oracal 651 items by series + code", () => {
    const item = findColorRegistryItem("ORACAL", "010", "651");
    expect(item?.series).toBe("651");
    expect(item?.translucent).not.toBe(true);
  });

  it("marks Oracal 8500 items as translucent", () => {
    const items = filterColorRegistry(ALL_COLOR_REGISTRY_ITEMS, {
      system: "ORACAL",
      series: "8500",
    });
    expect(items.length).toBeGreaterThan(0);
    expect(items.every((i) => i.translucent === true)).toBe(true);
  });

  it("filters by usageScope", () => {
    const face651 = filterColorRegistry(ALL_COLOR_REGISTRY_ITEMS, {
      system: "ORACAL",
      series: "651",
      usageScope: "face_vinyl",
    });
    expect(face651.length).toBeGreaterThan(0);
    expect(face651.every((i) => i.usageScope.includes("face_vinyl"))).toBe(true);

    const illuminated = filterColorRegistry(ALL_COLOR_REGISTRY_ITEMS, {
      system: "ORACAL",
      series: "8500",
      usageScope: "illuminated_face",
    });
    expect(illuminated.every((i) => i.series === "8500")).toBe(true);
  });

  it("searches by code and name", () => {
    const ral = searchColorRegistry(
      filterColorRegistry(ALL_COLOR_REGISTRY_ITEMS, { system: "RAL" }),
      "7016"
    );
    expect(ral.some((i) => i.code === "7016")).toBe(true);

    const oracal = searchColorRegistry(
      filterColorRegistry(ALL_COLOR_REGISTRY_ITEMS, { series: "651" }),
      "yellow"
    );
    expect(oracal.some((i) => i.code === "021")).toBe(true);
  });

  it("excludes inactive items when activeOnly is true", () => {
    const active = filterColorRegistry(
      [{ ...ALL_COLOR_REGISTRY_ITEMS[0], active: false }],
      { activeOnly: true }
    );
    expect(active).toHaveLength(0);
  });
});
