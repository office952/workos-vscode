import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import IntakeV6ReviewStatusStrip from "./IntakeV6ReviewStatusStrip";
import type { ReviewHandoffSurfacing } from "@/lib/intakeV6/intakeV6QuoteHandoffReadiness";

afterEach(() => cleanup());

const clearSurfacing: ReviewHandoffSurfacing = {
  showBanner: false,
  reasons: [],
  actions: [],
};

const blockerSurfacing: ReviewHandoffSurfacing = {
  showBanner: true,
  reasons: ["Confirmare operator lipsă"],
  actions: ["Confirmă setările în Review"],
};

describe("IntakeV6ReviewStatusStrip", () => {
  it("shows compact all-clear message", () => {
    render(<IntakeV6ReviewStatusStrip surfacing={clearSurfacing} />);
    expect(screen.getByTestId("intake-v6-review-status-strip-summary")).toHaveTextContent(
      /Toate setările tehnice sunt complete/,
    );
  });

  it("shows pending confirmation count and jump CTA", () => {
    const onJump = vi.fn();
    render(
      <IntakeV6ReviewStatusStrip
        surfacing={clearSurfacing}
        pendingConfirmationCount={2}
        onJumpToPending={onJump}
      />,
    );
    expect(screen.getByTestId("intake-v6-review-status-strip-summary")).toHaveTextContent(
      /Mai sunt 2 elemente de confirmat/,
    );
    fireEvent.click(screen.getByTestId("intake-v6-review-status-strip-jump"));
    expect(onJump).toHaveBeenCalledOnce();
  });

  it("expands blocker details on toggle", () => {
    render(<IntakeV6ReviewStatusStrip surfacing={blockerSurfacing} />);
    expect(screen.queryByTestId("intake-v6-review-status-strip-details")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-review-status-strip-toggle"));
    expect(screen.getByTestId("intake-v6-review-status-strip-details")).toHaveTextContent(
      /Confirmare operator lipsă/,
    );
  });
});
