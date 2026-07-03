import { describe, expect, it } from "vitest";
import {
  parseOrderConversionError,
  showsConversionSummary,
  showsConvertAction,
  showsInternalAcceptanceGuidance,
  QUOTE_CONVERT_BUTTON_LABEL,
} from "./quoteAcceptanceConversion";

describe("quoteAcceptanceConversion", () => {
  it("shows acceptance guidance for sent/viewed/negotiating", () => {
    expect(showsInternalAcceptanceGuidance("sent")).toBe(true);
    expect(showsInternalAcceptanceGuidance("priced")).toBe(false);
  });

  it("shows conversion summary for priced and accepted", () => {
    expect(showsConversionSummary("priced")).toBe(true);
    expect(showsConversionSummary("accepted")).toBe(true);
    expect(showsConversionSummary("sent")).toBe(false);
  });

  it("hides convert action for terminal quotes", () => {
    expect(showsConvertAction("rejected")).toBe(false);
    expect(showsConvertAction("expired")).toBe(false);
    expect(showsConvertAction("accepted")).toBe(true);
  });

  it("parses duplicate order conversion error", () => {
    const parsed = parseOrderConversionError(
      JSON.stringify({
        detail: {
          error: "order_already_exists_for_quote",
          existing_order_code: "ORD-123",
          existing_order_id: 55,
        },
      })
    );
    expect(parsed.error).toBe("order_already_exists_for_quote");
    expect(parsed.existingOrderCode).toBe("ORD-123");
    expect(parsed.existingOrderId).toBe(55);
  });

  it("uses clearer convert button label copy", () => {
    expect(QUOTE_CONVERT_BUTTON_LABEL).toMatch(/comandă/i);
    expect(QUOTE_CONVERT_BUTTON_LABEL).toMatch(/oferta activă/i);
  });
});
