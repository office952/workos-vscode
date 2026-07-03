import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { VolumetricQuoteReadinessChip } from "./VolumetricQuoteReadinessChip";
import type { QuoteReadinessSnapshot } from "@/lib/volumetricQuoteReady";

const baseSnapshot = (gate: QuoteReadinessSnapshot["quoteGate"]): QuoteReadinessSnapshot => ({
  templateCode: "TPL-VOLUMETRIC-LETTERS",
  quoteGate: gate,
});

describe("VolumetricQuoteReadinessChip", () => {
  it("renders Ready chip for clean gate", () => {
    render(
      <VolumetricQuoteReadinessChip
        snapshot={baseSnapshot({ can_create_commercial_quote: true, classified: {} })}
      />
    );
    const chip = screen.getByTestId("quote-volumetric-readiness-chip");
    expect(chip).toHaveTextContent("Ready");
    expect(chip).toHaveAttribute("data-readiness-status", "ready");
  });

  it("renders Requires acknowledgement with pending count", () => {
    render(
      <VolumetricQuoteReadinessChip
        snapshot={baseSnapshot({
          can_create_commercial_quote: true,
          requires_acknowledgement: true,
          classified: { acknowledgement_pending: ["operations_missing"] },
        })}
      />
    );
    expect(screen.getByTestId("quote-volumetric-readiness-chip")).toHaveTextContent(
      "Requires acknowledgement"
    );
    expect(screen.getByText(/1 ack pending/i)).toBeInTheDocument();
  });

  it("renders Blocked with blocker count", () => {
    render(
      <VolumetricQuoteReadinessChip
        snapshot={baseSnapshot({
          can_create_commercial_quote: false,
          blockers: ["letters_vector_file_required"],
          classified: { vector_blockers: ["letters_vector_file_required"] },
        })}
      />
    );
    expect(screen.getByTestId("quote-volumetric-readiness-chip")).toHaveTextContent("Blocked");
    expect(screen.getByText(/1 blocker/i)).toBeInTheDocument();
  });

  it("renders nothing when quote_gate is absent", () => {
    const { container } = render(<VolumetricQuoteReadinessChip snapshot={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing for non-volumetric snapshot", () => {
    const { container } = render(
      <VolumetricQuoteReadinessChip
        snapshot={{ templateCode: "TOTEM-ILUMINAT-STD", quoteGate: { can_create_commercial_quote: true } }}
      />
    );
    expect(container).toBeEmptyDOMElement();
  });
});
