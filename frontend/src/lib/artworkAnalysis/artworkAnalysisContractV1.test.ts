import { describe, expect, it } from "vitest";
import {
  ARTWORK_ANALYSIS_CONTRACT_VERSION,
  buildArtworkAnalysisReviewSurface,
  isSupportedArtworkAnalysisContractVersion,
  type ArtworkAnalysisContractV1,
} from "./artworkAnalysisContractV1";

describe("artworkAnalysisContractV1", () => {
  it("rejects unknown contract versions", () => {
    expect(isSupportedArtworkAnalysisContractVersion("artwork_analysis_contract_v99")).toBe(
      false,
    );
    expect(isSupportedArtworkAnalysisContractVersion(ARTWORK_ANALYSIS_CONTRACT_VERSION)).toBe(
      true,
    );
  });

  it("builds a read-only review surface that cannot write Product Truth", () => {
    const contract: ArtworkAnalysisContractV1 = {
      artwork_analysis_contract_version: ARTWORK_ANALYSIS_CONTRACT_VERSION,
      provenance: {
        analysis_id: "an-1",
        analysis_version: "1.0.0",
        source_file_hash: "sha256:x",
      },
      entities: [{ entity_id: "e1", status: "observed" }],
      observations: [{ observation_id: "o1", message: "layers", status: "observed" }],
      suggested_bindings: [
        { binding_id: "b1", status: "proposed", entity_ids: ["e1"] },
      ],
    };
    const surface = buildArtworkAnalysisReviewSurface(contract);
    expect(surface.product_truth_writable_from_adapter).toBe(false);
    expect(surface.all_bindings_proposed).toBe(true);
    expect(surface.unconfirmed_observation_count).toBe(1);
    expect(surface.transport).toBe("tbd");
  });
});
