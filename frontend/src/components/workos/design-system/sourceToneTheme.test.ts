import { describe, expect, it } from "vitest";
import { sourceEmptyToneClasses, sourceMixedToneClasses } from "./tokens";

describe("SourceBadge tone theme pairs", () => {
  it("sourceEmpty includes light surface + dark: pair", () => {
    expect(sourceEmptyToneClasses.bg).toMatch(/bg-emerald-50/);
    expect(sourceEmptyToneClasses.bg).toMatch(/dark:bg-emerald/);
    expect(sourceEmptyToneClasses.text).toMatch(/text-emerald-800/);
    expect(sourceEmptyToneClasses.text).toMatch(/dark:text-emerald/);
  });

  it("sourceMixed includes light surface + dark: pair", () => {
    expect(sourceMixedToneClasses.bg).toMatch(/bg-slate-100/);
    expect(sourceMixedToneClasses.bg).toMatch(/dark:bg-slate/);
    expect(sourceMixedToneClasses.text).toMatch(/text-slate-700/);
    expect(sourceMixedToneClasses.text).toMatch(/dark:text-slate/);
  });
});
