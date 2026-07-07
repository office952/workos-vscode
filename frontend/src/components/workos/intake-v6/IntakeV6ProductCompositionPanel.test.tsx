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

const linkedSegments = {
  root_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  segments: [
    {
      segment_key: "logo-stanga",
      parent_root_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      owning_template_code: "TPL-VOLUMETRIC-LOGO_v1",
      composition_role: "linked_logo_segment",
      binding_status: "suggested",
      product_truth_readiness: {
        ready_for_pricing: false,
        ready_for_quote: false,
        ready_for_order: false,
        ready_for_execution: false,
      },
    },
  ],
};

describe("IntakeV6ProductCompositionPanel", () => {
  it("renders Gradi as letters plus logo and confirms the composition", () => {
    const onConfirm = vi.fn();

    render(<IntakeV6ProductCompositionPanel payload={payload} onConfirm={onConfirm} />);

    expect(screen.getByText("Litere volumetrice + logo volumetric")).toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LOGO_v1")).toBeInTheDocument();
    expect(screen.getByText(/Straturi: Logo 1, Logo 2/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Confirma compozitia produsului/i }));

    expect(onConfirm).toHaveBeenCalledWith(payload.product_composition_recommendation.composition_items);
  });

  it("renders Product Definition linked segments as read-only composition summary", () => {
    render(<IntakeV6ProductCompositionPanel payload={payload} linkedSegments={linkedSegments} />);

    const summary = screen.getByTestId("intake-v6-product-definition-linked-segments");
    expect(summary).toHaveTextContent("Segmente legate Product Definition");
    expect(summary).toHaveTextContent("TPL-VOLUMETRIC-LETTERS_v2");
    expect(summary).toHaveTextContent("TPL-VOLUMETRIC-LOGO_v1");
    expect(summary).toHaveTextContent("Candidat compozitie, nu produs ofertabil separat");
    expect(summary).toHaveTextContent("Nu activeaza pricing, quote, order sau execution separat");
    expect(screen.queryByRole("button", { name: /oferta|comanda|execut/i })).not.toBeInTheDocument();
  });

  it("stays stable when linked Product Definition summary is missing", () => {
    render(<IntakeV6ProductCompositionPanel payload={payload} linkedSegments={null} />);

    expect(screen.queryByTestId("intake-v6-product-definition-linked-segments")).not.toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LOGO_v1")).toBeInTheDocument();
  });
});