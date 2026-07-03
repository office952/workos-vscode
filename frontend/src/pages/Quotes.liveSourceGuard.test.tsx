import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Quotes from "./Quotes";
import type { Quote } from "@/lib/mockData";

const mockUseBackendData = vi.fn();

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { role: "admin", name: "Admin", email: "admin@local" } }),
}));

vi.mock("@/hooks/useCompanyCommercialSettings", () => ({
  useCompanyCommercialSettings: () => ({
    vatPct: 21,
    eurToRonRate: 5,
    loading: false,
    error: null,
    reload: vi.fn(),
  }),
}));

vi.mock("@/components/workos/QuoteWizard", () => ({
  default: () => null,
}));

vi.mock("@/components/workos/QuoteRevisionDialog", () => ({
  default: () => null,
}));

vi.mock("@/lib/dataStore", () => ({
  updateQuoteStatus: vi.fn(),
  createOrderFromQuote: vi.fn(),
}));

const pricedQuote: Quote = {
  id: "QT-E2E-COMMERCIAL-001",
  dbId: 1,
  intakeId: "WI-E2E-COMMERCIAL-001",
  client: "E2E Commercial Spine Client",
  contactPerson: "E2E Validator",
  assignedTo: "Operator",
  status: "priced",
  version: 1,
  createdAt: "2026-06-01T00:00:00Z",
  validUntil: "2026-07-11",
  subtotal: 928.01,
  discount: 0,
  discountPct: 0,
  totalBeforeVAT: 928.01,
  vat: 176.32,
  grandTotal: 1104.33,
  marginPct: 25,
  lineItems: [],
  notes: "",
};

function renderQuoteDetail(
  quote: Quote,
  backendState: {
    source: "db" | "mixed" | "mock" | "empty" | "error";
    sourcesDetail?: Record<string, string>;
  }
) {
  mockUseBackendData.mockReturnValue({
    quotes: [quote],
    loading: false,
    error: null,
    source: backendState.source,
    sourcesDetail: backendState.sourcesDetail ?? {},
    refresh: vi.fn(),
  });

  return render(
    <MemoryRouter initialEntries={[`/quotes/${quote.id}`]}>
      <Routes>
        <Route path="/quotes/:quoteId?" element={<Quotes />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Quotes live source guard (sourcesDetail.quotes)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("enables commercial actions when quotes source is db but aggregate is mixed", async () => {
    renderQuoteDetail(pricedQuote, {
      source: "mixed",
      sourcesDetail: {
        intakes: "db",
        quotes: "db",
        orders: "empty",
        materials: "db",
        suppliers: "db",
      },
    });

    expect(
      await screen.findByTestId("quote-convert-action")
    ).not.toBeDisabled();
    expect(
      screen.queryByText(/necesită contract backend live/i)
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("quote-assisted-send-action")).not.toBeDisabled();
  });

  it("blocks commercial actions when quotes source is not db", async () => {
    renderQuoteDetail(pricedQuote, {
      source: "mixed",
      sourcesDetail: {
        quotes: "empty",
        orders: "empty",
      },
    });

    expect(await screen.findByTestId("quote-convert-action")).toBeDisabled();
    expect(
      screen.getByText(/Acțiunile comerciale sunt blocate: necesită contract backend live/i)
    ).toBeInTheDocument();
  });
});
