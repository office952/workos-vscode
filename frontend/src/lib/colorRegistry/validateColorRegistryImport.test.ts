import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  parseColorRegistryCsv,
  validateColorRegistryCsvFile,
  validateColorRegistryImportRows,
} from "./import/validateColorRegistryImport.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEMPLATE_CSV = readFileSync(
  join(__dirname, "import/color-registry-import.template.csv"),
  "utf8"
);

function validRow(overrides: Record<string, string> = {}) {
  return {
    system: "RAL",
    brand: "",
    series: "",
    code: "9010",
    name: "Pure White",
    romanianName: "Alb pur",
    previewHex: "#F7F9EF",
    finish: "matte",
    usageScope: "return;structure",
    translucent: "false",
    active: "true",
    source: "test_fixture",
    notes: "",
    __line: "2",
    ...overrides,
  };
}

describe("validateColorRegistryImport", () => {
  it("template CSV passes validation", () => {
    const result = validateColorRegistryCsvFile(TEMPLATE_CSV);
    expect(result.parseErrors).toEqual([]);
    expect(result.errors).toEqual([]);
    expect(result.ok).toBe(true);
    expect(result.items).toHaveLength(3);
  });

  it("parses CSV with quoted fields", () => {
    const csv = `system,code,name,previewHex,usageScope,translucent,active,source
RAL,9010,"Pure White",#FFFFFF,return,false,true,src`;
    const parsed = parseColorRegistryCsv(csv);
    expect(parsed.errors).toEqual([]);
    expect(parsed.rows[0].name).toBe("Pure White");
  });

  it("rejects duplicate system+series+code", () => {
    const result = validateColorRegistryImportRows([
      validRow(),
      validRow({ __line: "3" }),
    ]);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.includes("duplicate"))).toBe(true);
  });

  it("rejects invalid HEX", () => {
    const result = validateColorRegistryImportRows([
      validRow({ previewHex: "FFFFFF" }),
    ]);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.includes("previewHex"))).toBe(true);
  });

  it("rejects ORACAL without series", () => {
    const result = validateColorRegistryImportRows([
      validRow({
        system: "ORACAL",
        brand: "Oracal",
        series: "",
        translucent: "false",
      }),
    ]);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.includes("series"))).toBe(true);
  });

  it("rejects Oracal 8500 without translucent=true", () => {
    const result = validateColorRegistryImportRows([
      validRow({
        system: "ORACAL",
        brand: "Oracal",
        series: "8500",
        code: "010",
        translucent: "false",
        usageScope: "illuminated_face",
      }),
    ]);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.includes("8500"))).toBe(true);
  });

  it("rejects RAL with series", () => {
    const result = validateColorRegistryImportRows([
      validRow({ series: "651" }),
    ]);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.includes("RAL rows must not have series"))).toBe(
      true
    );
  });

  it("rejects unknown usageScope", () => {
    const result = validateColorRegistryImportRows([
      validRow({ usageScope: "invalid_scope" }),
    ]);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.includes("unknown usageScope"))).toBe(true);
  });

  it("requires source on every row", () => {
    const result = validateColorRegistryImportRows([validRow({ source: "" })]);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.includes("source is required"))).toBe(true);
  });
});
