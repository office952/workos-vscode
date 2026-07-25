import { describe, expect, it } from "vitest";
import {
  assertSablonLineMatchesOwnerLock,
  countAiProposedConnectionPrices,
  countOwnerLockedConnectionPrices,
  countOwnerVerifiedConnectionPrices,
  formatLettersAcmConnectionPriceRo,
  LETTERS_ACM_CONNECTION_PRICE_SHEET,
} from "./lettersAcmCompositionConnectionPrices";

describe("lettersAcmCompositionConnectionPrices", () => {
  it("lists all seven connection lines in order", () => {
    expect(LETTERS_ACM_CONNECTION_PRICE_SHEET.map((l) => l.order)).toEqual([1, 2, 3, 4, 5, 6, 7]);
    expect(LETTERS_ACM_CONNECTION_PRICE_SHEET.map((l) => l.id)).toEqual([
      "sablon_process",
      "fasten_forex_on_bond",
      "electric_psu_in_cassette",
      "supply_cable_5m_220v",
      "light_test",
      "attach_body_to_forex",
      "pack_composite",
    ]);
  });

  it("keeps șablon owner-locked; marks remaining owner-verified coherent", () => {
    expect(assertSablonLineMatchesOwnerLock()).toBe(true);
    expect(countOwnerLockedConnectionPrices()).toBe(1);
    expect(countOwnerVerifiedConnectionPrices()).toBe(6);
    expect(countAiProposedConnectionPrices()).toBe(0);
  });

  it("never uses hourly language and formats pack with minimum", () => {
    const prose = LETTERS_ACM_CONNECTION_PRICE_SHEET.map(
      (l) => `${l.labelRo} ${l.rationaleRo} ${formatLettersAcmConnectionPriceRo(l)}`,
    ).join(" ");
    expect(prose).not.toMatch(/\bEUR\/h\b|\bpe oră\b|\bpe ora\b|\b\/oră\b/i);
    const pack = LETTERS_ACM_CONNECTION_PRICE_SHEET.find((l) => l.id === "pack_composite");
    expect(formatLettersAcmConnectionPriceRo(pack!)).toBe("10 EUR/mp (min. 15 EUR)");
  });
});
