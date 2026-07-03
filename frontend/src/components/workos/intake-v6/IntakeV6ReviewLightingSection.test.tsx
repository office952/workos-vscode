import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6ReviewLightingSection from "./IntakeV6ReviewLightingSection";

const option = (value: string, label = value) => ({ value, label });

function renderLightingSection() {
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
      allowedLightingSystems={[option("led_modules", "Module LED")]}
      allowedLightColors={[option("neutral", "Neutral white")]}
      allowedLedModulePowerW={[option("0.75", "0.75 W / modul")]}
      allowedEmblemLightingModes={[option("area_lit", "Emblema luminoasa")]}
    />,
  );
}

describe("IntakeV6ReviewLightingSection component question labels", () => {
  it("renders electrical ownership and owner-approved cable defaults as display labels", () => {
    renderLightingSection();

    const badges = screen.getByTestId("intake-v6-electrical-component-badges");
    expect(badges).toHaveTextContent("Component: Electrical");
    expect(badges).toHaveTextContent("Product Truth candidate");
    expect(badges).toHaveTextContent("Included defaults: 1 m 2x0.75 + 5 m 2x1.5");
    expect(badges).toHaveTextContent("Commercial default: 1 m cable 2x0.75 for letters");
    expect(badges).toHaveTextContent("Commercial default: 5 m cable 2x1.5 final feed");
    expect(badges).toHaveTextContent("Extra cables/site details: order/execution");
    expect(badges).toHaveTextContent("Quote blocker conditional for special electrical/site scope");
    expect(badges).toHaveTextContent("Missing UI gap: cable routing and PSU placement");
    expect(badges).not.toHaveTextContent(/hour|minute|ora|oră|minut/i);
  });
});