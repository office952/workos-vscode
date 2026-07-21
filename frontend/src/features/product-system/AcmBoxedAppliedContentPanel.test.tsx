import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AcmBoxedAppliedContentPanel } from "./AcmBoxedAppliedContentPanel";

describe("AcmBoxedAppliedContentPanel", () => {
  it("renders XOR radios and optional frame for ACM boxed root", () => {
    render(
      <AcmBoxedAppliedContentPanel templateCode="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" />,
    );
    expect(screen.getByTestId("acm-boxed-applied-content-panel")).toBeInTheDocument();
    expect(screen.getByTestId("acm-applied-content-none")).toBeChecked();
    expect(screen.getByTestId("acm-metal-frame-checkbox")).not.toBeChecked();
  });

  it("does not render for other templates", () => {
    const { container } = render(
      <AcmBoxedAppliedContentPanel templateCode="TPL-VOLUMETRIC-LETTERS_v2" />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("enforces radio XOR and shows logo honesty note", () => {
    const onChange = vi.fn();
    render(
      <AcmBoxedAppliedContentPanel
        templateCode="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByTestId("acm-applied-content-logo"));
    expect(screen.getByTestId("acm-applied-content-logo")).toBeChecked();
    expect(screen.getByTestId("acm-applied-content-letters")).not.toBeChecked();
    expect(screen.getByTestId("acm-logo-branch-blocked-note")).toBeInTheDocument();
    expect(onChange).toHaveBeenCalledWith({
      appliedContent: "logo",
      metalFrameEnabled: false,
    });
  });

  it("toggles optional metal frame without auto thresholds", () => {
    const onChange = vi.fn();
    render(
      <AcmBoxedAppliedContentPanel
        templateCode="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByTestId("acm-metal-frame-checkbox"));
    expect(onChange).toHaveBeenLastCalledWith({
      appliedContent: "none",
      metalFrameEnabled: true,
    });
  });
});
