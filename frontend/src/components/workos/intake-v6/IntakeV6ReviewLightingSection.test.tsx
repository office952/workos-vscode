import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6ReviewLightingSection from "./IntakeV6ReviewLightingSection";

const option = (value: string, label = value) => ({ value, label });

function renderLightingSection(overrides: Partial<Parameters<typeof IntakeV6ReviewLightingSection>[0]> = {}) {
  render(
    <IntakeV6ReviewLightingSection
      illuminated
      onIlluminatedChange={vi.fn()}
      lightingSystemType="led_modules"
      onLightingSystemTypeChange={vi.fn()}
      lightColor="neutral"
      onLightColorChange={vi.fn()}
      ledModulePowerW={0.75}
      onLedModulePowerWChange={vi.fn()}
      ledDisplayPerimeterM={12.34}
      emblemLightingMode="area_lit"
      onEmblemLightingChange={vi.fn()}
      showEmblemLighting
      isLedModules
      ledModuleCount={40}
      emblemOutboxAreaM2={0.25}
      emblemLedModuleCount={8}
      emblemLightingModeNormalized="area_lit"
      totalLedModuleCount={48}
      letterLedStripLengthM={null}
      emblemLedStripLengthM={null}
      totalLedStripLengthM={null}
      ledStripPowerWPerMl={5}
      returnDepthMm={60}
      estimatedLedWatts={36}
      requiredPsuWatts={45}
      psuLabel="100W"
      psuAllocationStatus="ok"
      psuReservePercent={20}
      selectedPsuWatts={100}
      onSelectedPsuChange={vi.fn()}
      allowedPsuWatts={[60, 100, 160]}
      showLightingFields
      showElectricalFields
      allowedLightingSystems={[option("led_modules", "Module LED")]}
      allowedLightColors={[option("neutral", "Neutral white")]}
      allowedLedModulePowerW={[option("0.75", "0.75 W / modul")]}
      allowedEmblemLightingModes={[option("area_lit", "Emblema luminoasa")]}
      {...overrides}
    />,
  );
}

describe("IntakeV6ReviewLightingSection", () => {
  it("renders PSU selector in Electrica subsection", () => {
    renderLightingSection();
    expect(screen.getByTestId("intake-v6-electrical-subsection")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-selected-psu-watts")).toBeInTheDocument();
  });

  it("hides lighting fields when only electrical scope is sold", () => {
    renderLightingSection({ showLightingFields: false, showElectricalFields: true });
    expect(screen.queryByTestId("intake-v6-lighting-subsection")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-led-calc-readout")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-selected-psu-watts")).toBeInTheDocument();
  });

  it("hides electrical fields when only lighting scope is sold", () => {
    renderLightingSection({ showLightingFields: true, showElectricalFields: false });
    expect(screen.getByTestId("intake-v6-lighting-subsection")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-electrical-subsection")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-selected-psu-watts")).not.toBeInTheDocument();
  });
});
