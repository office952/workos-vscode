import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import AcmPanelProvisionalPricingBlock from "./AcmPanelProvisionalPricingBlock";
import type { AcmPanelCommercialPreview } from "@/lib/intakeV6/intakeV6PricedQuoteTypes";

const preview: AcmPanelCommercialPreview = {
  status: "provisional_with_warnings",
  currency: "EUR",
  estimated_total: 64.66,
  final_eligibility: false,
  offer_eligibility: false,
  execution_eligibility: false,
  geometry_summary: {
    assembly_width_mm: 2000,
    assembly_height_mm: 350,
    face_area_m2: 0.7,
    cut_length_m: 5.4,
    fold_length_m: 5.4,
    panel_count: 2,
  },
  warnings: ["technical_configuration_unconfirmed", "segmentation_proposed"],
  lines: [
    {
      code: "acm_panel_face_material",
      label: "Material ACM față panou",
      quantity: 0.7,
      unit: "m2",
      rate: 15,
      amount: 10.5,
      status: "provisional",
    },
    {
      code: "acm_panel_cut",
      label: "Debitare panou ACM",
      quantity: 5.4,
      unit: "ml",
      rate: 1.5,
      amount: 8.1,
      status: "provisional",
    },
  ],
};

describe("AcmPanelProvisionalPricingBlock", () => {
  it("renders provisional header, face area, and eligibility", () => {
    render(<AcmPanelProvisionalPricingBlock preview={preview} />);
    expect(screen.getByTestId("intake-v6-acm-panel-provisional-header")).toHaveTextContent(
      "Estimare provizorie AcmPanel",
    );
    expect(screen.getByTestId("intake-v6-acm-panel-face-area")).toHaveTextContent("0.7");
    expect(screen.getByTestId("intake-v6-acm-panel-eligibility-badges")).toHaveTextContent(
      "Offer ferm: indisponibil",
    );
    fireEvent.click(screen.getByTestId("intake-v6-acm-panel-breakdown-toggle"));
    expect(screen.getByTestId("intake-v6-acm-panel-line-acm_panel_cut")).toHaveAttribute(
      "data-provisional",
      "true",
    );
  });

  it("renders nothing without preview", () => {
    const { container } = render(<AcmPanelProvisionalPricingBlock preview={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});
