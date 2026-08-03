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

const confirmedPayload = {
  ...payload,
  product_composition_recommendation: {
    ...payload.product_composition_recommendation,
    status: "confirmed",
  },
  product_composition_confirmed: { confirmed: true },
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

const lettersPlusAcmPayload = {
  product_composition_recommendation: {
    status: "needs_confirmation",
    composition_type: "letters_plus_support",
    composition_items: [
      {
        composition_item_id: "letters",
        template_code: "TPL-VOLUMETRIC-LETTERS_v2",
        component_role: "volumetric_letters",
        source_layer_ids: ["letters"],
      },
      {
        composition_item_id: "support",
        template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        component_role: "support_panel",
        source_layer_ids: ["fundal-acm"],
      },
    ],
    warnings: [],
    blockers: [],
  },
  product_composition_confirmed: { confirmed: false },
};

describe("IntakeV6ProductCompositionPanel — F7E ACM inclusion honesty", () => {
  it("never shows the mandatory 'Inclus în propunere' copy for the ACM/support item", () => {
    render(<IntakeV6ProductCompositionPanel payload={lettersPlusAcmPayload} />);
    fireEvent.click(screen.getByTestId("intake-v6-product-composition-toggle"));

    expect(screen.getByTestId("intake-v6-product-composition-acm-inclusion-status")).toBeInTheDocument();
    expect(screen.queryAllByText("Inclus în propunere")).toHaveLength(1); // only the letters item
  });

  it("labels the ACM item as not yet priced when the payload does not price it into the offer", () => {
    render(<IntakeV6ProductCompositionPanel payload={lettersPlusAcmPayload} />);
    fireEvent.click(screen.getByTestId("intake-v6-product-composition-toggle"));

    expect(screen.getByTestId("intake-v6-product-composition-acm-inclusion-status")).toHaveTextContent(
      /nu este încă inclus în ofertă/i,
    );
  });

  it("labels the ACM item as actively priced when the payload prices it into the offer", () => {
    const payload = {
      ...lettersPlusAcmPayload,
      finish_setup: {
        mounting_solution: { template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" },
        applied_content: "letters",
      },
    };
    render(<IntakeV6ProductCompositionPanel payload={payload} />);
    fireEvent.click(screen.getByTestId("intake-v6-product-composition-toggle"));

    expect(screen.getByTestId("intake-v6-product-composition-acm-inclusion-status")).toHaveTextContent(
      /inclus activ în ofertă/i,
    );
  });

  it("A-F2: gives the optional ACM component its own include/exclude decision, separate from the mandatory confirm", () => {
    const onConfirm = vi.fn();
    render(<IntakeV6ProductCompositionPanel payload={lettersPlusAcmPayload} onConfirm={onConfirm} />);

    const toggle = screen.getByTestId("intake-v6-product-composition-acm-include-toggle").querySelector("input")!;
    expect(toggle).toBeChecked();

    fireEvent.click(toggle);
    expect(toggle).not.toBeChecked();

    fireEvent.click(screen.getByTestId("intake-v6-confirm-product-composition"));

    const confirmedItems = onConfirm.mock.calls[0][0] as Array<Record<string, unknown>>;
    expect(confirmedItems.some((item) => item.component_role === "support_panel")).toBe(false);
    expect(confirmedItems.some((item) => item.component_role === "volumetric_letters")).toBe(true);
  });

  it("A-F2: keeps the ACM component in the confirm payload when the operator leaves it included", () => {
    const onConfirm = vi.fn();
    render(<IntakeV6ProductCompositionPanel payload={lettersPlusAcmPayload} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByTestId("intake-v6-confirm-product-composition"));

    const confirmedItems = onConfirm.mock.calls[0][0] as Array<Record<string, unknown>>;
    expect(confirmedItems.some((item) => item.component_role === "support_panel")).toBe(true);
  });
});

describe("IntakeV6ProductCompositionPanel", () => {
  it("labels ACM panel-alone as Panou Alucobond casetat", () => {
    const supportOnly = {
      product_composition_recommendation: {
        status: "needs_confirmation",
        composition_type: "support_only",
        composition_items: [
          {
            composition_item_id: "support",
            template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
            component_role: "support_panel",
            source_layer_ids: ["Alucobond_x0020_Casetat"],
            status: "recommended",
          },
        ],
        warnings: [],
        blockers: [],
      },
      product_composition_confirmed: { confirmed: false },
      finish_setup: {
        acm_panel_instance: {
          schema: "acm_panel_component_instance_v1",
          composition_status: "unconfirmed",
        },
      },
    };

    render(<IntakeV6ProductCompositionPanel payload={supportOnly} />);

    expect(screen.getByTestId("intake-v6-product-composition-summary")).toHaveTextContent(
      "Panou Alucobond casetat",
    );
  });

  it("renders Gradi as letters plus logo and confirms the composition", () => {
    const onConfirm = vi.fn();

    render(<IntakeV6ProductCompositionPanel payload={payload} onConfirm={onConfirm} />);

    expect(screen.getByText("Litere volumetrice + logo volumetric")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-confirm-product-composition")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-product-composition-toggle")).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(screen.getByTestId("intake-v6-product-composition-toggle"));
    expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LOGO_v1")).toBeInTheDocument();
    expect(screen.getByText(/Straturi: Logo 1, Logo 2/i)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("intake-v6-confirm-product-composition"));

    expect(onConfirm).toHaveBeenCalledWith(payload.product_composition_recommendation.composition_items);
  });

  it("keeps Product Definition linked segments under technical disclosure", () => {
    render(<IntakeV6ProductCompositionPanel payload={payload} linkedSegments={linkedSegments} />);

    fireEvent.click(screen.getByTestId("intake-v6-product-composition-toggle"));
    const advanced = screen.getByTestId("intake-v6-product-composition-technical");
    expect(advanced).toHaveAttribute("data-expanded", "false");
    fireEvent.click(screen.getByTestId("intake-v6-product-composition-technical-toggle"));
    expect(advanced).toHaveAttribute("data-expanded", "true");
    expect(advanced).toHaveTextContent("TPL-VOLUMETRIC-LETTERS_v2");
    expect(advanced).toHaveTextContent("TPL-VOLUMETRIC-LOGO_v1");
    expect(advanced).toHaveTextContent(/Candidat compoziție|Candidat compozitie/i);
    expect(advanced).toHaveTextContent(/Nu activează pricing|Nu activeaza pricing/i);
    expect(screen.queryByRole("button", { name: /oferta|comanda|execut/i })).not.toBeInTheDocument();
  });

  it("stays stable when linked Product Definition summary is missing", () => {
    render(<IntakeV6ProductCompositionPanel payload={payload} linkedSegments={null} />);

    fireEvent.click(screen.getByTestId("intake-v6-product-composition-toggle"));
    expect(screen.queryByTestId("intake-v6-product-composition-technical")).not.toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(screen.getByText("TPL-VOLUMETRIC-LOGO_v1")).toBeInTheDocument();
  });

  it("collapses by default when already confirmed and can expand to show full details", () => {
    render(<IntakeV6ProductCompositionPanel payload={confirmedPayload} linkedSegments={linkedSegments} />);

    expect(screen.getByTestId("intake-v6-product-composition-toggle")).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByTestId("intake-v6-product-composition-summary")).toHaveTextContent("Litere volumetrice + logo volumetric");
    expect(screen.getByTestId("intake-v6-product-composition-linked-count")).toHaveTextContent(
      /1 segment legat/,
    );
    expect(screen.queryByTestId("intake-v6-product-composition-details")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("intake-v6-product-composition-toggle"));

    expect(screen.getByTestId("intake-v6-product-composition-toggle")).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("intake-v6-product-composition-details")).toBeInTheDocument();
    expect(screen.getAllByText("TPL-VOLUMETRIC-LETTERS_v2").length).toBeGreaterThan(0);
    expect(screen.getAllByText("TPL-VOLUMETRIC-LOGO_v1").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByTestId("intake-v6-product-composition-technical-toggle"));
    expect(screen.getByTestId("intake-v6-product-composition-technical")).toHaveTextContent(
      /Nu activează pricing|Nu activeaza pricing/i,
    );
  });

  it("keeps confirm CTA on L1 and demotes registry warnings into technical disclosure", () => {
    const withWarning = {
      ...payload,
      product_composition_recommendation: {
        ...payload.product_composition_recommendation,
        warnings: [
          {
            code: "LEGACY_SUPPORT_TEMPLATE",
            message: "Suport/fundal detectat; authority live este Alucobond casetat (TPL-ACM).",
          },
        ],
      },
    };
    render(<IntakeV6ProductCompositionPanel payload={withWarning} onConfirm={vi.fn()} />);

    expect(screen.getByTestId("intake-v6-confirm-product-composition")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-product-composition-toggle")).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText(/authority live/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-product-composition-toggle"));
    fireEvent.click(screen.getByTestId("intake-v6-product-composition-technical-toggle"));
    expect(screen.getByTestId("intake-v6-product-composition-issues")).toHaveTextContent(/authority live/i);
  });
});
