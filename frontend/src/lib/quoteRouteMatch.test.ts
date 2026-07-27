import { describe, expect, it } from "vitest";
import { matchQuoteByRouteParam } from "./quoteRouteMatch";

const quotes = [
  { id: "QT-2245", dbId: 5 },
  { id: "QT-9999", dbId: 12 },
  { id: "QT-NO-DB" },
];

describe("matchQuoteByRouteParam", () => {
  it("matches commercial quote code", () => {
    expect(matchQuoteByRouteParam(quotes, "QT-2245")?.id).toBe("QT-2245");
    expect(matchQuoteByRouteParam(quotes, "qt-2245")?.id).toBe("QT-2245");
  });

  it("matches numeric dbId deep-link", () => {
    expect(matchQuoteByRouteParam(quotes, "5")?.id).toBe("QT-2245");
    expect(matchQuoteByRouteParam(quotes, "12")?.id).toBe("QT-9999");
  });

  it("returns undefined for unknown ids", () => {
    expect(matchQuoteByRouteParam(quotes, "99")).toBeUndefined();
    expect(matchQuoteByRouteParam(quotes, "QT-MISSING")).toBeUndefined();
  });
});
