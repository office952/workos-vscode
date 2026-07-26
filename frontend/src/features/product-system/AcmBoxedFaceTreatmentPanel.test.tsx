import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AcmBoxedFaceTreatmentPanel } from "./AcmBoxedFaceTreatmentPanel";

describe("AcmBoxedFaceTreatmentPanel", () => {
  it("renders only for ACM boxed root", () => {
    const { container } = render(
      <AcmBoxedFaceTreatmentPanel templateCode="TPL-VOLUMETRIC-LETTERS_v2" />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows face-treatment section distinct from applied content", () => {
    render(
      <AcmBoxedFaceTreatmentPanel templateCode="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" />,
    );
    expect(screen.getByTestId("acm-boxed-face-treatment-panel")).toBeInTheDocument();
    expect(screen.getByText("Tratarea feței Bond/ACM")).toBeInTheDocument();
    expect(screen.getByTestId("acm-face-treatment-coexistence")).toHaveTextContent("none");
  });

  it("allows routed + insert coexistence and shows relief badge at 10 mm", () => {
    const onChange = vi.fn();
    render(
      <AcmBoxedFaceTreatmentPanel
        templateCode="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
        onChange={onChange}
      />,
    );

    fireEvent.click(screen.getByTestId("acm-face-treatment-routed-checkbox"));
    fireEvent.click(screen.getByTestId("acm-face-treatment-insert-checkbox"));

    expect(screen.getByTestId("acm-face-treatment-coexistence")).toHaveTextContent("both");
    expect(screen.getByTestId("acm-face-treatment-relief-badge")).toHaveTextContent(
      "RELIEF_PLEXI_10MM",
    );
    expect(screen.getByTestId("acm-face-treatment-optical-blocked-note")).toBeInTheDocument();
    expect(screen.getByTestId("acm-face-treatment-lines-allowed")).toHaveTextContent("false");
    expect(screen.getByTestId("acm-face-treatment-subtotal")).toHaveTextContent("BLOCKED");
    expect(screen.getByTestId("acm-face-treatment-scoped-blockers")).toHaveTextContent(
      "FACE_TREATMENT_OPTICAL_CATALOG_MISSING",
    );
    expect(screen.getByTestId("acm-face-treatment-scoped-blockers")).toHaveTextContent(
      "FACE_TREATMENT_ILLUMINATION_RATES_MISSING",
    );
    expect(onChange).toHaveBeenLastCalledWith({
      routedEnabled: true,
      insertEnabled: true,
      coexistence: "both",
      insertThicknessMm: 10,
    });
  });

  it("insert-only exposes optical blocker without illumination blocker", () => {
    render(
      <AcmBoxedFaceTreatmentPanel templateCode="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" />,
    );
    fireEvent.click(screen.getByTestId("acm-face-treatment-insert-checkbox"));
    expect(screen.getByTestId("acm-face-treatment-coexistence")).toHaveTextContent(
      "insert_only",
    );
    expect(screen.getByTestId("acm-face-treatment-scoped-blockers")).toHaveTextContent(
      "FACE_TREATMENT_OPTICAL_CATALOG_MISSING",
    );
    expect(screen.getByTestId("acm-face-treatment-scoped-blockers")).not.toHaveTextContent(
      "FACE_TREATMENT_ILLUMINATION_RATES_MISSING",
    );
    expect(screen.getByTestId("acm-face-treatment-subtotal")).toHaveTextContent("BLOCKED");
  });
});
