import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6ArtworkComplexityCard from "./IntakeV6ArtworkComplexityCard";

const assessment = {
  artwork_id: "raster:img1",
  source_element_type: "image" as const,
  source_layer_name: "maria",
  bounds: { x: 0, y: 0, width: 10, height: 10 },
  overlapped_vector_ids: ["letter-m"],
  dominant_color_count: 0,
  has_gradient: false,
  has_raster_image: true,
  has_external_image: true,
  has_clip_path: true,
  has_mask: false,
  has_transparency: true,
  has_many_colors: false,
  recommended_application: "print_on_vinyl_laminated" as const,
  recommendation_reason: "Raster over production geometry",
  artwork_area_estimate_m2: 0.12,
  artwork_area_source: "covered_vector_area_estimate",
  confidence: "estimated" as const,
  warnings: ["missing_external_image_asset"],
  artwork_role: "print_overlay" as const,
  image_href: "photo.png",
  external_image_detected: true,
  missing_external_image_asset: true,
};

describe("IntakeV6ArtworkComplexityCard", () => {
  it("displays recommendation and print laminate preview hint", () => {
    render(
      <IntakeV6ArtworkComplexityCard
        assessments={[assessment]}
        decisions={[
          {
            artwork_id: "raster:img1",
            operator_application: "print_on_vinyl_laminated",
            accepted_system_recommendation: true,
            override_manual_vinyl_cut: false,
          },
        ]}
        onDecisionChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Imprimare pe autocolant + laminare")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-print-laminate-visible")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-artwork-warning")).toHaveTextContent(
      "Logo/artwork raster extern lipsă",
    );
  });

  it("shows override state when operator chooses vinyl cut", () => {
    const onDecisionChange = vi.fn();
    render(
      <IntakeV6ArtworkComplexityCard
        assessments={[assessment]}
        decisions={[
          {
            artwork_id: "raster:img1",
            operator_application: "print_on_vinyl_laminated",
            accepted_system_recommendation: false,
            override_manual_vinyl_cut: false,
          },
        ]}
        onDecisionChange={onDecisionChange}
      />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-override-vinyl-cut"));
    expect(onDecisionChange).toHaveBeenCalled();
    const next = onDecisionChange.mock.calls[0][0] as Array<{ override_manual_vinyl_cut: boolean }>;
    expect(next[0].override_manual_vinyl_cut).toBe(true);
  });
});