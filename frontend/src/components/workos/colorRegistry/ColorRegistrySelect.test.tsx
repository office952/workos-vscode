import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import ColorRegistrySelect from "@/components/workos/colorRegistry/ColorRegistrySelect";

describe("ColorRegistrySelect", () => {
  it("renders swatch and calls onChange when option selected", () => {
    const onChange = vi.fn();
    render(
      <ColorRegistrySelect
        label="Test RAL"
        filter={{ system: "RAL", usageScope: "return" }}
        onChange={onChange}
        testId="test-color-select"
      />,
    );
    fireEvent.click(screen.getByTestId("test-color-select-choose"));
    expect(screen.getByTestId("test-color-select-list")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("test-color-select-search"), {
      target: { value: "9010" },
    });
    fireEvent.click(screen.getByTestId("test-color-select-option-RAL-ral-9010"));
    expect(onChange).toHaveBeenCalled();
    expect(onChange.mock.calls[0][0].code).toBe("9010");
  });

  it("shows selected color card when closed and hides search input", () => {
    render(
      <ColorRegistrySelect
        label="Test RAL"
        valueCode="9010"
        filter={{ system: "RAL", usageScope: "return" }}
        onChange={vi.fn()}
        testId="test-color-select"
      />,
    );
    expect(screen.getByTestId("test-color-select-selected")).toBeInTheDocument();
    expect(screen.getByTestId("test-color-select-trigger")).toBeInTheDocument();
    expect(screen.getByTestId("test-color-select-change")).toBeInTheDocument();
    expect(screen.queryByTestId("test-color-select-search")).not.toBeInTheDocument();
    expect(screen.queryByTestId("test-color-select-list")).not.toBeInTheDocument();
  });

  it("opens list on trigger click without typing search", () => {
    render(
      <ColorRegistrySelect
        label="Test RAL"
        valueCode="9010"
        filter={{ system: "RAL", usageScope: "return" }}
        onChange={vi.fn()}
        testId="test-color-select"
      />,
    );
    fireEvent.click(screen.getByTestId("test-color-select-change"));
    expect(screen.getByTestId("test-color-select-panel")).toBeInTheDocument();
    expect(screen.getByTestId("test-color-select-list")).toBeInTheDocument();
    expect(screen.getByTestId("test-color-select-search")).toBeInTheDocument();
    const list = screen.getByTestId("test-color-select-list");
    expect(within(list).getAllByRole("button").length).toBeGreaterThan(1);
  });

  it("filters list when search is used inside open panel", () => {
    render(
      <ColorRegistrySelect
        label="Test RAL"
        filter={{ system: "RAL", usageScope: "return" }}
        onChange={vi.fn()}
        testId="test-color-select"
      />,
    );
    fireEvent.click(screen.getByTestId("test-color-select-choose"));
    fireEvent.change(screen.getByTestId("test-color-select-search"), {
      target: { value: "9010" },
    });
    expect(screen.getByTestId("test-color-select-option-RAL-ral-9010")).toBeInTheDocument();
    expect(screen.queryByTestId("test-color-select-option-RAL-ral-9005")).not.toBeInTheDocument();
  });

  it("differentiates 651 from 8500 in options", () => {
    render(
      <ColorRegistrySelect
        label="Face 8500"
        filter={{ system: "ORACAL", series: "8500", usageScope: "illuminated_face" }}
        onChange={vi.fn()}
        testId="test-8500-select"
      />,
    );
    fireEvent.click(screen.getByTestId("test-8500-select-choose"));
    expect(screen.getByTestId("test-8500-select-list")).toBeInTheDocument();
    expect(screen.getByTestId("test-8500-select-option-ORACAL-8500-010")).toBeInTheDocument();
  });

  it("shows approximate note for RAL when closed", () => {
    render(
      <ColorRegistrySelect
        label="RAL"
        filter={{ system: "RAL" }}
        onChange={vi.fn()}
        showApproxNote
        testId="test-ral-note"
      />,
    );
    expect(screen.getByTestId("test-ral-note-approx-note")).toBeInTheDocument();
    expect(screen.queryByTestId("test-ral-note-search")).not.toBeInTheDocument();
  });

  it("closes panel after selecting a color", () => {
    const onChange = vi.fn();
    render(
      <ColorRegistrySelect
        label="Test RAL"
        valueCode="9005"
        filter={{ system: "RAL", usageScope: "return" }}
        onChange={onChange}
        testId="test-color-select"
      />,
    );
    fireEvent.click(screen.getByTestId("test-color-select-change"));
    fireEvent.click(screen.getByTestId("test-color-select-option-RAL-ral-9010"));
    expect(onChange).toHaveBeenCalled();
    expect(screen.queryByTestId("test-color-select-panel")).not.toBeInTheDocument();
    expect(screen.queryByTestId("test-color-select-search")).not.toBeInTheDocument();
  });

  it("uses fixed-height color row with equally sized Schimba button", () => {
    render(
      <ColorRegistrySelect
        label="Test Oracal"
        valueCode="010"
        filter={{ system: "ORACAL", series: "651", usageScope: "face_vinyl" }}
        onChange={vi.fn()}
        testId="test-oracal-select"
      />,
    );
    const row = screen.getByTestId("test-oracal-select-row");
    const trigger = screen.getByTestId("test-oracal-select-trigger");
    const change = screen.getByTestId("test-oracal-select-change");
    expect(row).toHaveClass("h-9");
    expect(trigger).toHaveClass("h-9");
    expect(change).toHaveClass("h-9", "w-[4.75rem]");
    expect(change).toHaveTextContent("Schimbă");
  });

  it("hides redundant 651 colored badge when Oracal code is already visible", () => {
    render(
      <ColorRegistrySelect
        label="Culoare față"
        valueCode="010"
        filter={{ system: "ORACAL", series: "651", usageScope: "face_vinyl" }}
        onChange={vi.fn()}
        testId="test-651-select"
      />,
    );
    expect(screen.getByTestId("test-651-select-trigger")).toHaveTextContent("Oracal 651-010");
    expect(screen.queryByText("651 colored")).not.toBeInTheDocument();
  });
});
