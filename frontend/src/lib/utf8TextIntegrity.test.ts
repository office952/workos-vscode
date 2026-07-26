import { describe, expect, it } from "vitest";
import { assertNoMojibake, hasSuspiciousMojibake } from "./utf8TextIntegrity";

const CLEAN = [
  "ă â î ș ț",
  "Ă Â Î Ș Ț",
  "față",
  "șablon",
  "manoperă",
  "aplicare folie pe fețe",
  "tăiere",
  "îndoire",
  "vopsire",
  "execuție",
  "operație",
  "cantitate",
  "preț",
  "măsură",
  "en dash –",
  "em dash —",
  "euro €",
  "multiplication ×",
  "area m²",
];

describe("utf8TextIntegrity", () => {
  it("accepts clean Romanian and symbols", () => {
    for (const sample of CLEAN) {
      expect(hasSuspiciousMojibake(sample)).toBe(false);
      expect(() => assertNoMojibake(sample)).not.toThrow();
    }
  });

  it("flags confirmed mojibake samples", () => {
    expect(hasSuspiciousMojibake("faÈ›Äƒ")).toBe(true);
    expect(hasSuspiciousMojibake("ManoperÄƒ")).toBe(true);
    expect(hasSuspiciousMojibake("È™ablon")).toBe(true);
    expect(hasSuspiciousMojibake("â€”")).toBe(true);
    expect(() => assertNoMojibake("PregÄƒtire", "task")).toThrow(/mojibake/);
  });

  it("does not treat lone Romanian capitals as mojibake", () => {
    expect(hasSuspiciousMojibake("Ă Â Î Ș Ț")).toBe(false);
  });
});
