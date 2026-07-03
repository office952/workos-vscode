import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { VolumetricCommercialReadinessPanel } from "./VolumetricCommercialReadinessPanel";
import type { VolumetricQuoteGate } from "@/lib/volumetricQuoteReady";

const readyGate: VolumetricQuoteGate = {
  can_create_commercial_quote: true,
  requires_acknowledgement: false,
  warnings: ["vector_analysis_pending"],
  classified: {
    warnings: ["vector_analysis_pending"],
    acknowledgement_pending: [],
  },
};

const ackGate: VolumetricQuoteGate = {
  can_create_commercial_quote: true,
  requires_acknowledgement: true,
  warnings: ["operations_missing"],
  classified: {
    warnings: ["operations_missing"],
    acknowledgement_pending: ["operations_missing"],
  },
  reason_codes: ["acknowledgement_required:operations_missing"],
};

const blockedGate: VolumetricQuoteGate = {
  can_create_commercial_quote: false,
  requires_acknowledgement: false,
  blockers: ["letters_vector_file_required"],
  classified: {
    vector_blockers: ["letters_vector_file_required"],
  },
};

describe("VolumetricCommercialReadinessPanel", () => {
  it("shows Ready with warnings status and informational warnings", () => {
    render(<VolumetricCommercialReadinessPanel gate={readyGate} />);
    expect(screen.getByTestId("volumetric-commercial-readiness-status")).toHaveTextContent(
      "Ready with warnings"
    );
    expect(screen.getByTestId("volumetric-commercial-readiness-warnings")).toBeInTheDocument();
    expect(screen.getByText(/vector_analysis_pending/)).toBeInTheDocument();
  });

  it("shows Requires acknowledgement and ack control", () => {
    const onChange = vi.fn();
    render(
      <VolumetricCommercialReadinessPanel
        gate={ackGate}
        showAcknowledgementControl
        acknowledgementChecked={false}
        onAcknowledgementChange={onChange}
      />
    );
    expect(screen.getByTestId("volumetric-commercial-readiness-status")).toHaveTextContent(
      "Requires acknowledgement"
    );
    expect(screen.getByTestId("volumetric-commercial-readiness-ack-pending")).toBeInTheDocument();
    const checkbox = screen.getByRole("checkbox");
    fireEvent.click(checkbox);
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it("shows Blocked status and blockers distinct from warnings", () => {
    render(<VolumetricCommercialReadinessPanel gate={blockedGate} />);
    expect(screen.getByTestId("volumetric-commercial-readiness-status")).toHaveTextContent(
      "Blocked"
    );
    expect(screen.getByTestId("volumetric-commercial-readiness-blockers")).toBeInTheDocument();
    expect(
      screen.queryByTestId("volumetric-commercial-readiness-ack-pending")
    ).not.toBeInTheDocument();
  });

  it("shows no-ack compact state when conversion allowed without ack", () => {
    render(
      <VolumetricCommercialReadinessPanel
        gate={readyGate}
        showAcknowledgementControl
      />
    );
    expect(screen.getByTestId("volumetric-commercial-readiness-no-ack")).toHaveTextContent(
      /No acknowledgement required/i
    );
  });
});
