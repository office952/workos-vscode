import { describe, expect, it } from "vitest";
import {
  COST_INTERN_ESTIMATIV_LABEL,
  OFERTA_CLIENT_LABEL,
  OFERTA_VS_COST_BOUNDARY_HELP,
  REGISTRY_INTERN_LABEL,
} from "./intakeV6OfferCostChromeVocabulary";
import {
  INTAKE_V6_LIVE_CALC_INTERNAL_LABEL,
  INTAKE_V6_LIVE_CALC_TITLE,
} from "@/components/workos/intake-v6/IntakeV6LiveCalculationSummary";

describe("intakeV6OfferCostChromeVocabulary", () => {
  it("keeps Ofertă client distinct from Cost intern estimativ", () => {
    expect(OFERTA_CLIENT_LABEL).toBe("Ofertă client");
    expect(COST_INTERN_ESTIMATIV_LABEL).toBe("Cost intern estimativ");
    expect(OFERTA_CLIENT_LABEL).not.toBe(COST_INTERN_ESTIMATIV_LABEL);
    expect(REGISTRY_INTERN_LABEL).toMatch(/Registry/i);
    expect(OFERTA_VS_COST_BOUNDARY_HELP).toMatch(/Ofertă client/i);
    expect(OFERTA_VS_COST_BOUNDARY_HELP).toMatch(/Cost intern/i);
  });

  it("wires live-calc chrome constants to offer/cost vocabulary", () => {
    expect(INTAKE_V6_LIVE_CALC_TITLE).toBe(OFERTA_CLIENT_LABEL);
    expect(INTAKE_V6_LIVE_CALC_INTERNAL_LABEL).toBe(COST_INTERN_ESTIMATIV_LABEL);
  });
});
