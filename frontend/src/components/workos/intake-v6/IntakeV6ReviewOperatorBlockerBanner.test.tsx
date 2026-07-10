import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import IntakeV6ReviewOperatorBlockerBanner from "./IntakeV6ReviewOperatorBlockerBanner";
import type { OperatorBlockerBannerDisplay } from "@/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay";

afterEach(() => cleanup());

const blockedDisplay: OperatorBlockerBannerDisplay = {
  show: true,
  loading: false,
  messages: [
    "Referințele straturilor selectate lipsesc. Verifică selecția straturilor în Pasul 1.",
  ],
  severity: "blocked",
  hasTechnicalBlockers: true,
};

describe("IntakeV6ReviewOperatorBlockerBanner", () => {
  it("renders operator messages without raw codes", () => {
    render(<IntakeV6ReviewOperatorBlockerBanner display={blockedDisplay} />);
    expect(screen.getByTestId("intake-v6-review-operator-blocker-banner")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-review-operator-blocker-messages")).toHaveTextContent(
      /Referințele straturilor selectate lipsesc/i,
    );
    expect(screen.getByTestId("intake-v6-review-operator-blocker-messages")).not.toHaveTextContent(
      /SELECTED_LAYER_REFS_MISSING/,
    );
  });

  it("calls diagnostic jump handler", () => {
    const onJump = vi.fn();
    render(
      <IntakeV6ReviewOperatorBlockerBanner display={blockedDisplay} onJumpToDiagnostic={onJump} />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-review-operator-blocker-diagnostic-link"));
    expect(onJump).toHaveBeenCalledOnce();
  });

  it("renders nothing when display.show is false", () => {
    render(
      <IntakeV6ReviewOperatorBlockerBanner
        display={{ ...blockedDisplay, show: false, messages: [] }}
      />,
    );
    expect(screen.queryByTestId("intake-v6-review-operator-blocker-banner")).not.toBeInTheDocument();
  });
});
