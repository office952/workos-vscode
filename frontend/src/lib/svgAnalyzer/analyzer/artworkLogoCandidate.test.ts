import { describe, expect, it } from "vitest";
import { isArtworkOrLogoCandidateLayer } from "./artworkLogoCandidate";

describe("isArtworkOrLogoCandidateLayer", () => {
  it("detects logo_instance and stroke origins", () => {
    expect(
      isArtworkOrLogoCandidateLayer({
        id: "logo_instance_001",
        name: "Logo 1",
        layerOrigin: "stroke_vector_outline",
        autoRole: "printed_artwork",
        roleGuess: "printed_artwork",
      }),
    ).toBe(true);
  });

  it("does not treat solid fill ACM panel as artwork", () => {
    expect(
      isArtworkOrLogoCandidateLayer({
        id: "pseudo:fill-c5c6c6",
        name: "pseudo fill-c5c6c6",
        layerOrigin: "solid_fill_cluster",
        autoRole: "support_panel",
        roleGuess: "support_panel",
      }),
    ).toBe(false);
  });
});
