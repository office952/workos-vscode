import { describe, expect, it } from "vitest";
import { LETTERS_ACM_COMPOSITION_TASK_CHAIN } from "./lettersAcmCompositionTaskOrder";

describe("lettersAcmCompositionTaskOrder", () => {
  it("is strictly ordered 1..8 with unique ids", () => {
    expect(LETTERS_ACM_COMPOSITION_TASK_CHAIN.map((t) => t.order)).toEqual([
      1, 2, 3, 4, 5, 6, 7, 8,
    ]);
    expect(new Set(LETTERS_ACM_COMPOSITION_TASK_CHAIN.map((t) => t.id)).size).toBe(8);
  });

  it("starts with ACM finish without pack and ends with composite pack", () => {
    expect(LETTERS_ACM_COMPOSITION_TASK_CHAIN[0]!.id).toBe("acm_finish_no_pack");
    expect(LETTERS_ACM_COMPOSITION_TASK_CHAIN[0]!.labelRo).toMatch(/fără impachetare/i);
    expect(LETTERS_ACM_COMPOSITION_TASK_CHAIN.at(-1)!.id).toBe("pack_composite");
  });

  it("places șablon process before Forex fasten and electric before body attach", () => {
    const ids = LETTERS_ACM_COMPOSITION_TASK_CHAIN.map((t) => t.id);
    expect(ids.indexOf("sablon_process_on_bond")).toBeLessThan(ids.indexOf("fasten_forex_on_bond"));
    expect(ids.indexOf("light_test")).toBeLessThan(ids.indexOf("attach_body_to_forex_on_bond"));
    expect(ids.indexOf("electric_inside_bond_psu")).toBeLessThan(
      ids.indexOf("attach_body_to_forex_on_bond"),
    );
  });

  it("teaches 20 EUR/mp on șablon and integral outbox basis", () => {
    const sablon = LETTERS_ACM_COMPOSITION_TASK_CHAIN.find((t) => t.id === "sablon_process_on_bond");
    expect(sablon?.costNoteRo).toBe("20 EUR/mp");
    expect(sablon?.meaningRo).toMatch(/layer integral/i);
    expect(sablon?.meaningRo).toMatch(/nu sumă piesă cu piesă/i);
  });
});
