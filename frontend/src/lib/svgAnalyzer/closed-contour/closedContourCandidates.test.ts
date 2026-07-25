import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "../analyzer/analyzeSvg";
import {
  assertContourIdentityStable,
  detectClosedContourCandidates,
} from "./closedContourCandidates";
import {
  blankPreviewMm,
  buildAcmMountingSolutionFromSelection,
  casingRequirementsActive,
  confirmAlucobondSelection,
  emptySvgSupportSelection,
  reconcileSelectionAfterReanalysis,
} from "./alucobondCasedPanelSelection";

const REAL_FIXTURE =
  process.env.WORKOS_ACP_SVG_FIXTURE ??
  "C:/Users/offic/Desktop/fisiere-teste-svg/LITERE-VOLUMETRICE-ACP.svg";

describe("closed contour candidates", () => {
  it("A/C/D detects closed path Z, rect, polygon without color authority", () => {
    const svg = `<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="80mm" viewBox="0 0 100 80">
  <rect x="5" y="5" width="90" height="70" fill="none" stroke="#000"/>
  <path d="M20 20 L40 20 L40 40 L20 40 Z" fill="#f00"/>
  <polygon points="50,20 70,20 70,45 50,45" fill="#0f0"/>
</svg>`;
    const { parsed, report } = analyzeSvgString(svg, "unit.svg", svg.length);
    const cc = report.closedContourCandidates!;
    expect(cc.closed_contour_count).toBeGreaterThanOrEqual(3);
    const types = new Set(cc.candidates.map((c) => c.source_element_type));
    expect(types.has("rect")).toBe(true);
    expect(types.has("polygon")).toBe(true);
    expect(cc.candidates.some((c) => c.closure_method === "explicit_z")).toBe(true);
    // Outer rect should outrank letter-sized path
    const top = cc.candidates[0];
    expect(top.source_element_type).toBe("rect");
    expect(top.is_outer_candidate).toBe(true);
    expect(top.reasons.join(" ")).toMatch(/contur închis|candidat panou/i);
    void parsed;
  });

  it("L demotes letter holes / small contours vs outer panel", () => {
    const svg = `<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="100mm" viewBox="0 0 200 100">
  <polygon points="0,0 200,0 200,100 0,100" fill="none" stroke="#111"/>
  <path d="M30 30 L50 30 L50 50 L30 50 Z M35 35 L45 35 L45 45 L35 45 Z" fill="#00a"/>
</svg>`;
    const { report } = analyzeSvgString(svg, "holes.svg", svg.length);
    const cc = report.closedContourCandidates!;
    const outer = cc.candidates.find((c) => c.source_element_type === "polygon");
    expect(outer).toBeTruthy();
    expect(outer!.contains_count).toBeGreaterThanOrEqual(1);
    expect(outer!.confidence).toBeGreaterThan(
      cc.candidates.find((c) => c.source_element_type === "path_subpath" || c.source_element_type === "path")
        ?.confidence ?? 0,
    );
  });

  it("P/Q deterministic ordering + reasons", () => {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="50mm" height="50mm" viewBox="0 0 50 50">
      <circle cx="25" cy="25" r="20" fill="none" stroke="#000"/>
    </svg>`;
    const a = analyzeSvgString(svg, "c.svg", 10);
    const b = analyzeSvgString(svg, "c.svg", 10);
    expect(assertContourIdentityStable(a.report.closedContourCandidates!, b.report.closedContourCandidates!)).toBe(
      true,
    );
    expect(a.report.closedContourCandidates!.candidates[0].reasons.length).toBeGreaterThan(0);
  });

  it("AH/AI/AL casing profile + blank preview + inactive isolation", () => {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="60mm" viewBox="0 0 100 60">
      <rect x="0" y="0" width="100" height="60" fill="none" stroke="#000"/>
    </svg>`;
    const { report } = analyzeSvgString(svg, "p.svg", 10);
    const cand = report.closedContourCandidates!.candidates[0];
    const ok2 = confirmAlucobondSelection({
      candidate: cand,
      svg_source_hash: "abc",
      fold_count: 2,
      l1_mm: 60,
      l2_mm: 25,
      service_corner: "TOP_RIGHT",
      internal_frame_enabled: true,
      unit_ambiguity: false,
    });
    expect(ok2.blockers).toEqual([]);
    expect(ok2.selection.casing_profile?.finished_depth_mm).toBe(60);
    expect(ok2.selection.casing_profile?.l2_mm).toBe(25);
    const blank = blankPreviewMm({
      width_mm: cand.width_mm,
      height_mm: cand.height_mm,
      fold_count: 2,
      l1_mm: 60,
      l2_mm: 25,
    });
    // fold_sum = 85; +10 mm CNC fixing margin (owner 2026-07-23)
    expect(blank.cnc_fixing_margin_mm).toBe(10);
    expect(blank.blank_width_mm).toBe(cand.width_mm + 2 * 85 + 10);

    const bad = confirmAlucobondSelection({
      candidate: cand,
      svg_source_hash: "abc",
      fold_count: 2,
      l1_mm: 60,
      l2_mm: null,
      service_corner: "TOP_LEFT",
      internal_frame_enabled: false,
      unit_ambiguity: false,
    });
    expect(bad.blockers.length).toBeGreaterThan(0);

    const one = confirmAlucobondSelection({
      candidate: cand,
      svg_source_hash: "abc",
      fold_count: 1,
      l1_mm: 40,
      l2_mm: null,
      service_corner: null,
      internal_frame_enabled: false,
      unit_ambiguity: false,
    });
    expect(one.blockers).toEqual([]);
    expect(one.selection.casing_profile?.l2_mm).toBeNull();

    expect(casingRequirementsActive(emptySvgSupportSelection())).toBe(false);
    expect(casingRequirementsActive(ok2.selection)).toBe(true);

    const mount = buildAcmMountingSolutionFromSelection(ok2.selection);
    expect(mount?.template_code).toBe("TPL-ACM-BOXED-MOUNTING-SUPPORT_v1");
    expect((mount?.configuration as Record<string, unknown>).return_depth_mm).toBe(60);
    expect((mount?.configuration as Record<string, unknown>).rear_lip_mm).toBe(25);
  });

  it("AW changed SVG invalidates selection", () => {
    const svg1 = `<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="60mm" viewBox="0 0 100 60"><rect width="100" height="60"/></svg>`;
    const { report } = analyzeSvgString(svg1, "a.svg", 10);
    const cand = report.closedContourCandidates!.candidates[0];
    const { selection } = confirmAlucobondSelection({
      candidate: cand,
      svg_source_hash: "hash-a",
      fold_count: 2,
      l1_mm: 60,
      l2_mm: 25,
      service_corner: "BOTTOM_LEFT",
      internal_frame_enabled: false,
      unit_ambiguity: false,
    });
    const next = reconcileSelectionAfterReanalysis({
      previous: selection,
      current_svg_source_hash: "hash-b",
      candidates: report.closedContourCandidates!.candidates,
    });
    expect(next.status).toBe("reconfirm_required");
  });
});

describe("real ACP fixture (external, optional)", () => {
  const available = existsSync(REAL_FIXTURE);

  it.skipIf(!available)("S–Y real file: panel candidate, letters separate, no mutation", () => {
    const before = createHash("sha256").update(readFileSync(REAL_FIXTURE)).digest("hex");
    const source = readFileSync(REAL_FIXTURE, "utf8");
    const { report } = analyzeSvgString(source, "LITERE-VOLUMETRICE-ACP.svg", source.length);
    const cc = report.closedContourCandidates!;
    expect(cc.closed_contour_count).toBeGreaterThanOrEqual(3);
    const top = cc.candidates[0];
    expect(top.source_element_type).toBe("polygon");
    expect(top.contains_count).toBeGreaterThanOrEqual(5);
    expect(top.is_outer_candidate).toBe(true);
    // Letters remain as separate closed contours
    expect(cc.candidates.some((c) => c.source_element_type === "path_subpath")).toBe(true);
    expect(cc.unit_ambiguity).toBe(true);
    expect(top.width_mm).toBeGreaterThan(1000);
    expect(top.width_mm).toBeLessThan(3000);
    const after = createHash("sha256").update(readFileSync(REAL_FIXTURE)).digest("hex");
    expect(after).toBe(before);
    const second = analyzeSvgString(source, "LITERE-VOLUMETRICE-ACP.svg", source.length);
    expect(assertContourIdentityStable(cc, second.report.closedContourCandidates!)).toBe(true);
  });
});
