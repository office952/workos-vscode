import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import IntakeV6ReviewOperatorBlockerBanner from "./IntakeV6ReviewOperatorBlockerBanner";
import type { OperatorBlockerBannerDisplay } from "@/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay";

afterEach(() => cleanup());

const blockedDisplay: OperatorBlockerBannerDisplay = {
  show: true,
  loading: false,
  summaryTitle: "Configurarea necesită atenție · 1 blocant",
  blockerCount: 1,
  warningCount: 0,
  messages: [
    "Referințele straturilor selectate lipsesc. Verifică selecția straturilor în Pasul 1.",
  ],
  issues: [
    {
      id: "tech-SELECTED_LAYER_REFS_MISSING",
      severity: "blocker",
      code: "SELECTED_LAYER_REFS_MISSING",
      message: "Referințele straturilor selectate lipsesc. Verifică selecția straturilor în Pasul 1.",
      action: "Rezolvă câmpul marcat în Review / Pasul 1.",
      focusTarget: null,
    },
  ],
  severity: "blocked",
  hasTechnicalBlockers: true,
};

describe("IntakeV6ReviewOperatorBlockerBanner", () => {
  it("renders compact summary without footer-next-step duplication", () => {
    render(<IntakeV6ReviewOperatorBlockerBanner display={blockedDisplay} />);
    expect(screen.getByTestId("intake-v6-review-operator-blocker-banner-title")).toHaveTextContent(
      /Configurarea necesită atenție · 1 blocant/i,
    );
    expect(screen.getByTestId("intake-v6-review-operator-blocker-banner")).toHaveAttribute(
      "data-attention-weight",
      "compact",
    );
    expect(screen.queryByTestId("intake-v6-review-operator-blocker-footer-hint")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-review-operator-blocker-expand-hint")).toHaveTextContent(/Deschide lista/i);
    expect(screen.queryByTestId("intake-v6-review-operator-blocker-compact-one")).not.toBeInTheDocument();
  });

  it("expands to show issue details without raw-only generic panel", () => {
    render(<IntakeV6ReviewOperatorBlockerBanner display={blockedDisplay} />);
    fireEvent.click(screen.getByTestId("intake-v6-review-operator-blocker-banner-toggle"));
    expect(screen.getByTestId("intake-v6-review-operator-blocker-messages")).toHaveTextContent(
      /Referințele straturilor selectate lipsesc/i,
    );
  });

  it("calls diagnostic jump handler when list is expanded", () => {
    const onJump = vi.fn();
    render(
      <IntakeV6ReviewOperatorBlockerBanner display={blockedDisplay} onJumpToDiagnostic={onJump} />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-review-operator-blocker-banner-toggle"));
    fireEvent.click(screen.getByTestId("intake-v6-review-operator-blocker-diagnostic-link"));
    expect(onJump).toHaveBeenCalledOnce();
  });

  it("renders nothing when display.show is false", () => {
    render(
      <IntakeV6ReviewOperatorBlockerBanner
        display={{ ...blockedDisplay, show: false, messages: [], issues: [] }}
      />,
    );
    expect(screen.queryByTestId("intake-v6-review-operator-blocker-banner")).not.toBeInTheDocument();
  });
});
