import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { buildProductTruthDraft } from "@/lib/intakeV6/productTruth/productTruthDraftBuilder";
import { gradiCuratCompleteReviewLikeFixture } from "@/lib/intakeV6/productTruth/productTruthFixtures";
import { mapReturnCantTruthFieldsReadonly } from "@/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper";
import IntakeV6ReturnCantBlockedStateAwarenessPanel from "./IntakeV6ReturnCantBlockedStateAwarenessPanel";

describe("IntakeV6ReturnCantBlockedStateAwarenessPanel", () => {
  it("shows operator-facing missing-value guidance without technical confirmation wording", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);
    const model = mapReturnCantTruthFieldsReadonly({
      productTruthDraft: draft,
      quoteGeometry: {
        letter_perimeter_m: 21.1675,
        geometry_source: "nest2_face_parts_outer",
        confirmed: true,
      },
    });

    render(<IntakeV6ReturnCantBlockedStateAwarenessPanel model={model} />);

    expect(screen.getByTestId("intake-v6-return-cant-blocked-awareness")).toHaveAttribute(
      "data-variant",
      "operator",
    );
    expect(screen.getByText("Return/cant necesită valori obligatorii lipsă.")).toBeInTheDocument();
    expect(screen.getByText("OPERATOR_ACTION_REQUIRED")).toBeInTheDocument();
    expect(screen.getByText("RETURN_CANT_MATERIAL_MISSING")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-return-cant-perimeter-path")).toHaveTextContent(
      "quote_geometry.letter_perimeter_m",
    );
    expect(screen.queryByText(/preview ready/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/calculation ready/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/pret final/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/total estimat/i)).not.toBeInTheDocument();
  });

  it("shows technical diagnostics separately when variant is technicalOnly", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);
    const model = mapReturnCantTruthFieldsReadonly({
      productTruthDraft: draft,
      quoteGeometry: {
        letter_perimeter_m: 21.1675,
        geometry_source: "nest2_face_parts_outer",
        confirmed: true,
      },
    });

    render(<IntakeV6ReturnCantBlockedStateAwarenessPanel model={model} variant="technicalOnly" />);

    expect(screen.getByTestId("intake-v6-return-cant-blocked-awareness")).toHaveAttribute(
      "data-variant",
      "technicalOnly",
    );
    expect(screen.getByText("Detalii tehnice return/cant (read-only).")).toBeInTheDocument();
    expect(screen.getByText("TECHNICAL_ONLY")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-return-cant-context-only-line")).toHaveTextContent(
      "Perimetru din quote_geometry",
    );
    expect(screen.getByTestId("intake-v6-return-cant-face-dependency-line")).toHaveTextContent(
      "components.face.confirmed_perimeter",
    );
    expect(screen.getByTestId("intake-v6-return-cant-confirmation-line")).toHaveTextContent(
      "Stare componentă:",
    );
  });
});
