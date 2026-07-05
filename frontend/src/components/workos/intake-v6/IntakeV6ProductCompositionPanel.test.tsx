import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import IntakeV6ProductCompositionPanel from "./IntakeV6ProductCompositionPanel";

const payload = {
  product_composition_recommendation: {
    status: "needs_confirmation",
    composition_type: "letters_plus_logo",
    composition_items: [
      {
        composition_item_id: "letters",
        template_code: "TPL-VOLUMETRIC-LETTERS_v2",
        component_role: "volumetric_letters",
        source_layer_ids: ["letters"],
      },
      {
        composition_item_id: "logo",
        template_code: "TPL-VOLUMETRIC-LOGO_v1",
        component_role: "volumetric_logo",
        source_layer_ids: ["logo-stanga", "logo-dreapta"],
      },
    ],
    warnings: [],
    blockers: [],
  },
  product_composition_confirmed: { confirmed: false },
};

describe("IntakeV6ProductCompositionPanel", () => {
  it("renders Gradi as letters plus logo and confirms the composition", () => {
    const onConfirm = vi.fn();

    render(<IntakeV6ProductCompositionPanel payload={payload} onConfirm={onConfirm} />);

    expect(screen.getByText("Litere volumetrice + logo volumetric")).toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LOGO_v1")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Confirma compozitia produsului/i }));

    expect(onConfirm).toHaveBeenCalledWith(payload.product_composition_recommendation.composition_items);
  });
});