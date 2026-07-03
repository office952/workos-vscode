import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import IntakeV6ReturnCantFields from "./IntakeV6ReturnCantFields";

vi.mock("@/components/workos/colorRegistry/ColorRegistrySelect", () => ({
  default: ({
    label,
    testId,
    onChange,
  }: {
    label: string;
    testId?: string;
    onChange: (item: { code: string; name: string } | null) => void;
  }) => (
    <button type="button" data-testid={testId} onClick={() => onChange({ code: "9005", name: "Jet black" })}>
      {label}
    </button>
  ),
}));

describe("IntakeV6ReturnCantFields", () => {
  it("renders only simplified cant finish options", () => {
    render(
      <IntakeV6ReturnCantFields
        idPrefix="test"
        returnCant={{ finishType: "standard_aluminum", depthMm: 60 }}
        onReturnChange={vi.fn()}
        testIdPrefix="intake-v6-return"
      />,
    );

    const options = Array.from(
      screen.getByTestId("intake-v6-return-type").querySelectorAll("option"),
    ).map((node) => node.textContent);
    expect(options).toEqual(["Alb", "Negru", "Auriu", "Argintiu", "Vopsit RAL", "Oracal 651"]);
  });

  it("defaults cant UI to Alb when finish type is missing", () => {
    render(
      <IntakeV6ReturnCantFields
        idPrefix="test"
        returnCant={{ finishType: "white_aluminum", depthMm: 60 }}
        onReturnChange={vi.fn()}
        testIdPrefix="intake-v6-return"
      />,
    );
    expect(screen.getByTestId("intake-v6-return-type")).toHaveValue("white");
  });

  it("shows RAL selector when Vopsit RAL is selected", () => {
    const onReturnChange = vi.fn();
    render(
      <IntakeV6ReturnCantFields
        idPrefix="test"
        returnCant={{ finishType: "ral_paint", depthMm: 60 }}
        onReturnChange={onReturnChange}
        testIdPrefix="intake-v6-return"
      />,
    );

    expect(screen.getByTestId("intake-v6-return-ral-select")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-return-ral-select"));
    expect(onReturnChange).toHaveBeenCalledWith(
      expect.objectContaining({
        finishType: "ral_paint",
        materialCode: "RAL",
        colorCode: "9005",
      }),
    );
  });

  it("persists oracal_wrapped + 651 when Oracal 651 is selected", () => {
    const onReturnChange = vi.fn();
    const { rerender } = render(
      <IntakeV6ReturnCantFields
        idPrefix="test"
        returnCant={{ finishType: "white_aluminum", depthMm: 60 }}
        onReturnChange={onReturnChange}
        testIdPrefix="intake-v6-return"
      />,
    );

    fireEvent.change(screen.getByTestId("intake-v6-return-type"), {
      target: { value: "oracal_wrapped" },
    });
    expect(onReturnChange).toHaveBeenCalledWith(
      expect.objectContaining({
        finishType: "oracal_wrapped",
        materialCode: "651",
      }),
    );

    rerender(
      <IntakeV6ReturnCantFields
        idPrefix="test"
        returnCant={{ finishType: "oracal_wrapped", depthMm: 60, materialCode: "651" }}
        onReturnChange={onReturnChange}
        testIdPrefix="intake-v6-return"
      />,
    );
    expect(screen.getByTestId("intake-v6-return-oracal651")).toBeInTheDocument();
    expect(screen.getByText("Culoare Oracal 651 cant / volum")).toBeInTheDocument();
  });

  it("does not show Return or Colantat in operator-facing labels", () => {
    render(
      <IntakeV6ReturnCantFields
        idPrefix="test"
        returnCant={{ finishType: "oracal_wrapped", depthMm: 60, materialCode: "651" }}
        onReturnChange={vi.fn()}
        testIdPrefix="intake-v6-return"
      />,
    );

    const visibleText = document.body.textContent ?? "";
    expect(visibleText).not.toMatch(/\bReturn\b/);
    expect(visibleText).not.toContain("Colantat");
    expect(screen.getByText("Tip finisaj cant / volum")).toBeInTheDocument();
  });
});