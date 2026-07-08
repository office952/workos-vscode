import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { buildProductTruthDraft } from "@/lib/intakeV6/productTruth/productTruthDraftBuilder";
import { gradiCuratCompleteReviewLikeFixture } from "@/lib/intakeV6/productTruth/productTruthFixtures";
import { mapReturnCantTruthFieldsReadonly } from "@/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper";
import IntakeV6ReturnCantBlockedStateAwarenessPanel from "./IntakeV6ReturnCantBlockedStateAwarenessPanel";

describe("IntakeV6ReturnCantBlockedStateAwarenessPanel", () => {
  it("shows the blocked return/cant diagnostic without preview or pricing claims", () => {
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

    expect(screen.getByTestId("intake-v6-return-cant-blocked-awareness")).toBeInTheDocument();
    expect(screen.getByText("Return/cant component preview este blocat.")).toBeInTheDocument();
    expect(
      screen.getByText(/Motiv: datele necesare nu sunt inca confirmate pe componenta\./),
    ).toBeInTheDocument();
    expect(screen.getByText("RETURN_CANT_MAPPER_BLOCKED")).toBeInTheDocument();
    expect(screen.getByText("RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-return-cant-context-only-line")).toHaveTextContent(
      "quote_geometry.letter_perimeter_m",
    );
    expect(screen.getByTestId("intake-v6-return-cant-face-dependency-line")).toHaveTextContent(
      "components.face.confirmed_perimeter",
    );
    expect(screen.getByTestId("intake-v6-return-cant-confirmation-line")).toHaveTextContent(
      "components.return_cant.confirmation_state = confirmed",
    );
    expect(screen.getByTestId("intake-v6-return-cant-perimeter-path")).toHaveTextContent(
      "quote_geometry.letter_perimeter_m",
    );
    expect(screen.queryByText(/preview ready/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/calculation ready/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/pret final/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/total estimat/i)).not.toBeInTheDocument();
  });
});