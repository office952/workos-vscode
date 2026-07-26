import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";
import {
  proposeSegmentedBackgroundFromCandidates,
  selectNearbySupportCandidates,
} from "./segmentedBackground";
import type { ClosedContourCandidate } from "@/lib/svgAnalyzer/closed-contour/closedContourTypes";

describe("real desktop SVG candidates", () => {
  it("proposes from case1 closed contours snapshot", () => {
    const p = path.resolve(
      __dirname,
      "../../../../docs/qa/segmented-background-live-e2e-2026-07-19/runtime/case1_workspace_after_import.json",
    );
    const snap = JSON.parse(fs.readFileSync(p, "utf8"));
    const cands = snap.closed_contours.candidates as ClosedContourCandidate[];
    const group = selectNearbySupportCandidates(cands);
    const proposal = proposeSegmentedBackgroundFromCandidates(cands);
    expect(group.length).toBeGreaterThanOrEqual(2);
    expect(proposal).not.toBeNull();
    expect(proposal!.panels.length).toBeGreaterThanOrEqual(2);
    expect(proposal!.status).toBe("PROPOSED");
  });
});
