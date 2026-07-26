import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ArtworkAnalysisReviewPanel } from "./ArtworkAnalysisReviewPanel";
import type { ArtworkAnalysisReviewSurfaceV1 } from "@/lib/artworkAnalysis/artworkAnalysisContractV1";

describe("ArtworkAnalysisReviewPanel", () => {
  it("shows empty state when no external analysis is present", () => {
    render(<ArtworkAnalysisReviewPanel />);
    expect(screen.getByTestId("artwork-analysis-review-empty")).toBeTruthy();
    expect(screen.getByText(/aplicației desktop/i)).toBeTruthy();
  });

  it("renders read-only surface without Product Truth write affordance", () => {
    const surface: ArtworkAnalysisReviewSurfaceV1 = {
      analysis_id: "an-9",
      contract_version: "artwork_analysis_contract_v1",
      source_file_name: "demo.svg",
      source_file_hash: "sha256:1",
      entity_count: 2,
      group_count: 1,
      measurement_count: 0,
      observation_count: 1,
      suggested_binding_count: 1,
      unconfirmed_observation_count: 1,
      all_bindings_proposed: true,
      product_truth_writable_from_adapter: false,
      transport: "tbd",
      notes: ["Operatorul confirmă."],
    };
    render(<ArtworkAnalysisReviewPanel surface={surface} />);
    expect(screen.getByTestId("artwork-analysis-review-surface")).toBeTruthy();
    expect(screen.getByText(/blocat \(consume-only\)/i)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /confirm/i })).toBeNull();
  });
});
