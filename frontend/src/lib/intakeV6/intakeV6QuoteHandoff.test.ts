import { describe, expect, it } from "vitest";

import {
  buildIntakeProductSpecFromV6QuoteInput,
  buildV6QuoteWizardNavState,
} from "./intakeV6QuoteHandoff";

describe("intakeV6QuoteHandoff", () => {
  it("maps quote_input geometry and lighting to product spec", () => {
    const spec = buildIntakeProductSpecFromV6QuoteInput({
      letter_count: 12,
      letter_perimeter_m: 18.5,
      face_area_m2: 2.1,
      return_depth_mm: 60,
      illuminated: true,
      lighting_system_type: "led_modules",
      estimated_led_watts: 120,
      required_psu_watts: 160,
      psu_configuration: [160],
      face_finish_type: "vinyl",
    });
    expect(spec.letter_count).toBe(12);
    expect(spec.letter_perimeter_m).toBe(18.5);
    expect(spec.return_depth_mm).toBe(60);
    expect(spec.lighting_system_type).toBe("led_modules");
    expect(spec.selected_psu_watts).toBe(160);
  });

  it("builds QuoteWizard nav state with openWizard", () => {
    const state = buildV6QuoteWizardNavState({
      quoteInput: { letter_count: 5, letter_perimeter_m: 9 },
      clientName: "HUB MEDIA",
    });
    expect(state.openWizard).toBe(true);
    expect(state.fromIntake).toBe(true);
    expect(state.clientName).toBe("HUB MEDIA");
    expect(state.productSpec?.letter_count).toBe(5);
  });
});