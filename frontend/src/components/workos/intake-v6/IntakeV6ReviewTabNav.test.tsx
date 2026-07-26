import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6ReviewTabNav from "./IntakeV6ReviewTabNav";

describe("IntakeV6ReviewTabNav", () => {
  it("shows Finisaje pending badge but no redundant Iluminare ON pill", () => {
    render(
      <IntakeV6ReviewTabNav
        active="finisaje"
        onChange={vi.fn()}
        templateCode="TPL-VOLUMETRIC-LETTERS_v2"
        pendingFinisaje={2}
        illuminated
      />,
    );

    expect(screen.getByTestId("intake-v6-review-tab-finisaje-pending")).toHaveTextContent("2");
    expect(screen.queryByTestId("intake-v6-review-tab-iluminare-active")).not.toBeInTheDocument();
    expect(screen.queryByText("ON")).not.toBeInTheDocument();
  });

  it("switches tabs on click", () => {
    const onChange = vi.fn();
    render(
      <IntakeV6ReviewTabNav
        active="finisaje"
        onChange={onChange}
        templateCode="TPL-VOLUMETRIC-LETTERS_v2"
      />,
    );

    fireEvent.click(screen.getByTestId("intake-v6-review-tab-iluminare"));
    expect(onChange).toHaveBeenCalledWith("iluminare");
  });

  it("renders vertical domain split for montaj", () => {
    render(
      <IntakeV6ReviewTabNav
        active="panou_carcasa"
        onChange={vi.fn()}
        templateCode="TPL-VOLUMETRIC-LETTERS_v2"
        orientation="vertical"
      />,
    );

    expect(screen.getByTestId("intake-v6-review-tabs")).toHaveAttribute(
      "data-orientation",
      "vertical",
    );
    expect(screen.getByTestId("intake-v6-review-tabs")).toHaveAttribute(
      "aria-orientation",
      "vertical",
    );
    expect(screen.getByTestId("intake-v6-review-tab-panou_carcasa")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-review-tab-montaj_comercial")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-review-tab-montaj")).not.toBeInTheDocument();
  });

  it("defaults to horizontal orientation for bottom strip", () => {
    render(
      <IntakeV6ReviewTabNav
        active="finisaje"
        onChange={vi.fn()}
        templateCode="TPL-VOLUMETRIC-LETTERS_v2"
      />,
    );

    expect(screen.getByTestId("intake-v6-review-tabs")).toHaveAttribute(
      "data-orientation",
      "horizontal",
    );
    expect(screen.getByTestId("intake-v6-review-tabs")).toHaveAttribute(
      "aria-orientation",
      "horizontal",
    );
    expect(screen.getByTestId("intake-v6-review-tab-panou_carcasa")).toBeInTheDocument();
  });
});
