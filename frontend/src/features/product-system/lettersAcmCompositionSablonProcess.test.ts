import { describe, expect, it } from "vitest";
import {
  formatLettersAcmSablonProcessRateRo,
  LETTERS_ACM_SABLON_AREA_BASIS_ID,
  LETTERS_ACM_SABLON_AREA_BASIS_RO,
  LETTERS_ACM_SABLON_BUNDLED_STEPS_RO,
  LETTERS_ACM_SABLON_PROCESS_RATE_EUR_PER_MP,
} from "./lettersAcmCompositionSablonProcess";

describe("lettersAcmCompositionSablonProcess", () => {
  it("locks owner bundled rate at 20 EUR/mp", () => {
    expect(LETTERS_ACM_SABLON_PROCESS_RATE_EUR_PER_MP).toBe(20);
    expect(formatLettersAcmSablonProcessRateRo()).toBe("20 EUR/mp");
  });

  it("uses integral letters-layer outbox, not per-piece sum", () => {
    expect(LETTERS_ACM_SABLON_AREA_BASIS_ID).toBe("letters_layer_outbox_integral");
    expect(LETTERS_ACM_SABLON_AREA_BASIS_RO).toMatch(/layer integral/i);
    expect(LETTERS_ACM_SABLON_AREA_BASIS_RO).toMatch(/nu sumă piesă cu piesă/i);
  });

  it("bundles five atelier steps under one commercial process", () => {
    expect(LETTERS_ACM_SABLON_BUNDLED_STEPS_RO).toHaveLength(5);
    expect(LETTERS_ACM_SABLON_BUNDLED_STEPS_RO.join(" ")).toMatch(/cutter|plotter/i);
    expect(LETTERS_ACM_SABLON_BUNDLED_STEPS_RO.join(" ")).toMatch(/transfer/i);
  });
});
