import { fireEvent, render, screen } from "@testing-library/react";
import IntakeV6BackingAndEmblemSection from "./IntakeV6BackingAndEmblemSection";

describe("IntakeV6BackingAndEmblemSection", () => {
  it("shows required backing options and active emblem lighting control", () => {
    const onBacking = vi.fn();
    const onEmblem = vi.fn();
    render(
      <IntakeV6BackingAndEmblemSection
        backingMode="forex_10_no_bevel"
        emblemLightingMode="area_lit"
        onBackingChange={onBacking}
        onEmblemLightingChange={onEmblem}
      />,
    );

    expect(screen.getByTestId("intake-v6-backing-section")).toBeInTheDocument();
    expect(screen.getByText("Spate / backing litere")).toBeInTheDocument();
    expect(screen.getByText(/Plexiglas 3 mm/)).toBeInTheDocument();

    const backingSelect = screen.getByTestId("intake-v6-backing-mode");
    expect(backingSelect).toHaveDisplayValue("Forex 10 mm fara sanfren");
    expect(screen.queryByRole("option", { name: /Fara spate|Fără spate/i })).not.toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Forex 10 mm fara sanfren" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Forex 10 mm cu sanfren" })).toBeInTheDocument();

    const emblemSelect = screen.getByTestId("intake-v6-emblem-lighting-mode");
    expect(emblemSelect).toHaveDisplayValue("Emblema luminoasa - calcul pe arie");
    expect(screen.queryByRole("option", { name: /Decizie/i })).not.toBeInTheDocument();
    expect(screen.getByText(/volum 60 mm: gol 40 mm pe linie si 80 mm pe coloana/)).toBeInTheDocument();
  });

  it("calls handlers on change", () => {
    const onBacking = vi.fn();
    const onEmblem = vi.fn();
    render(
      <IntakeV6BackingAndEmblemSection
        backingMode="forex_10_no_bevel"
        emblemLightingMode="area_lit"
        onBackingChange={onBacking}
        onEmblemLightingChange={onEmblem}
      />,
    );

    fireEvent.change(screen.getByTestId("intake-v6-backing-mode"), {
      target: { value: "forex_10_with_bevel" },
    });
    expect(onBacking).toHaveBeenCalledWith("forex_10_with_bevel");

    fireEvent.change(screen.getByTestId("intake-v6-emblem-lighting-mode"), {
      target: { value: "excluded" },
    });
    expect(onEmblem).toHaveBeenCalledWith("excluded");
  });
});