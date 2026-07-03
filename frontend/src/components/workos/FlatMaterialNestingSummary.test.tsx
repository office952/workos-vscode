import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import FlatMaterialNestingSummary from "./FlatMaterialNestingSummary";

describe("FlatMaterialNestingSummary", () => {
  it("shows rest placă estimat not pierdere", () => {
    render(
      <FlatMaterialNestingSummary
        summary={{
          sheet_materials: [
            {
              role: "plexiglass_face",
              label: "Plexiglas față 3 mm",
              enabled: true,
              sheets_used: 1,
              allocated_sheet_area_m2: 6.19,
              used_piece_bbox_area_m2: 1.25,
              remaining_area_m2: 4.94,
              remaining_percent: 79.8,
              profile_source_label: "fallback intern",
              is_default_fallback: true,
              sheet_width_mm: 3050,
              sheet_height_mm: 2030,
              pieces_count: 6,
              nesting_method: "sheet_rectangular",
            },
          ],
          real_offcut_measurement_required: true,
        }}
      />,
    );
    expect(screen.getByText(/Rest placă estimat/i)).toBeInTheDocument();
    expect(screen.queryByText(/Pierdere estimată/i)).toBeNull();
    expect(screen.getByText(/Restul real se măsoară/i)).toBeInTheDocument();
  });
});
