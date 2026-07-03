import { describe, expect, it } from "vitest";
import { parsePathMetrics } from "@/lib/svgPathMetrics";

describe("svgPathMetrics", () => {
  it("parses simple closed rectangle", () => {
    const r = parsePathMetrics("M0 0 L100 0 L100 50 L0 50 Z");
    expect(r.subpathCount).toBe(1);
    expect(r.totalLength).toBeCloseTo(300, 0);
    expect(r.totalClosedArea).toBeCloseTo(5000, 0);
  });

  it("parses multiple subpaths with zm", () => {
    const r = parsePathMetrics("M0 0 L10 0 L10 10 Z m20 0 L30 0 L30 10 Z");
    expect(r.subpathCount).toBe(2);
    expect(r.totalClosedArea).toBeGreaterThan(0);
  });

  it("parses relative lowercase commands", () => {
    const r = parsePathMetrics("m 0 0 l 100 0 l 0 50 l -100 0 z");
    expect(r.totalLength).toBeCloseTo(300, 0);
    expect(r.totalClosedArea).toBeCloseTo(5000, 0);
  });

  it("parses H/V commands", () => {
    const r = parsePathMetrics("M 0 0 H 100 V 50 H 0 Z");
    expect(r.totalLength).toBeCloseTo(300, 0);
    expect(r.totalClosedArea).toBeCloseTo(5000, 0);
  });

  it("parses cubic curves with approximate warning", () => {
    const r = parsePathMetrics("M0 0 C 25 0, 75 50, 100 50 L 100 0 Z");
    expect(r.totalLength).toBeGreaterThan(0);
    expect(r.warnings.some((w) => w.includes("approximat") || w.includes("Arc"))).toBe(true);
  });

  it("parses comma-separated Corel-style coordinates", () => {
    const r = parsePathMetrics("m0,0 l10,0 l0,10 l-10,0z");
    expect(r.totalClosedArea).toBeCloseTo(100, 0);
  });
});
