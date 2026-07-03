import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import IntakeWorkTypePicker from "./IntakeWorkTypePicker";

const REGISTRY = [
  { id: 1, family_id: "litere_volumetrice", label: "Litere volumetrice", active: true },
  { id: 2, family_id: "print_large_format", label: "Print format mare", active: true },
  { id: 3, family_id: "casete_luminoase", label: "Casete luminoase", active: true },
];

describe("IntakeWorkTypePicker", () => {
  it("renders human-readable labels without internal codes as primary text", () => {
    render(
      <IntakeWorkTypePicker
        selectedWorkTypeId={null}
        onSelect={vi.fn()}
        registry={REGISTRY}
      />
    );

    expect(screen.getByText("Litere volumetrice")).toBeInTheDocument();
    expect(screen.queryByText("litere_volumetrice")).not.toBeInTheDocument();
  });

  it("calls onSelect when an enabled card is clicked", () => {
    const onSelect = vi.fn();
    render(
      <IntakeWorkTypePicker
        selectedWorkTypeId={null}
        onSelect={onSelect}
        registry={REGISTRY}
      />
    );

    fireEvent.click(screen.getByRole("radio", { name: /Litere volumetrice/i }));
    expect(onSelect).toHaveBeenCalledWith("volumetric");
  });
});
