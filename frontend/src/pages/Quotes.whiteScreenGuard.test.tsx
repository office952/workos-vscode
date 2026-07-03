import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Quotes from "./Quotes";
import type { Quote } from "@/lib/mockData";

const mockUseBackendData = vi.fn();
const mockUseAuth = vi.fn();

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
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

vi.mock("@/lib/dataStore", () => ({
  updateQuoteStatus: vi.fn(),
  createOrderFromQuote: vi.fn(),
}));

const baseQuote: Quote = {
  id: "QT-GUARD-001",
  client: "Client Test",
  contactPerson: "Contact",
  assignedTo: "Operator",
  status: "priced",
  version: 1,
  createdAt: "2026-06-01T00:00:00Z",
  validUntil: "2026-07-01",
  subtotal: 100,
  discount: 0,
  discountPct: 0,
  totalBeforeVAT: 100,
  vat: 19,
  grandTotal: 119,
  marginPct: 25,
  lineItems: [],
  notes: "",
};

function renderQuotes(path = "/quotes") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/quotes/:quoteId?" element={<Quotes />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Quotes white screen guard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: { role: "admin", name: "Admin", email: "admin@local" },
    });
    mockUseBackendData.mockReturnValue({
      quotes: [baseQuote],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { quotes: "db" },
      refresh: vi.fn(),
    });
  });

  it("renders list without white screen when quotes load successfully", () => {
    renderQuotes();
    expect(screen.getByText(/Selectează o ofertă/i)).toBeInTheDocument();
    expect(screen.getByText("QT-GUARD-001")).toBeInTheDocument();
  });

  it("shows controlled access message for employee_mobile on quotes API error", () => {
    mockUseAuth.mockReturnValue({
      user: { role: "employee_mobile", name: "Sandu", email: "sandu@local" },
    });
    mockUseBackendData.mockReturnValue({
      quotes: [],
      loading: false,
      error: "HTTP 403 Forbidden",
      source: "error",
      sourcesDetail: { quotes: "error" },
      refresh: vi.fn(),
    });

    renderQuotes();
    expect(screen.getByTestId("quotes-access-denied")).toBeInTheDocument();
    expect(screen.getByText(/Nu ai acces la pagina Oferte/i)).toBeInTheDocument();
  });

  it("does not white screen when quote has unknown status", () => {
    mockUseBackendData.mockReturnValue({
      quotes: [{ ...baseQuote, status: "unknown_status" as Quote["status"] }],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { quotes: "db" },
      refresh: vi.fn(),
    });

    renderQuotes();
    expect(screen.getByText("unknown_status")).toBeInTheDocument();
  });

  it("does not white screen when client and currency are partially missing", () => {
    mockUseBackendData.mockReturnValue({
      quotes: [
        {
          ...baseQuote,
          client: "",
          currency: undefined,
          grandTotal: 0,
        },
      ],
      loading: false,
      error: null,
      source: "db",
      sourcesDetail: { quotes: "db" },
      refresh: vi.fn(),
    });

    renderQuotes();
    expect(screen.getByText("QT-GUARD-001")).toBeInTheDocument();
  });

  it("shows backend error banner without crashing when API returns 500", () => {
    mockUseBackendData.mockReturnValue({
      quotes: [],
      loading: false,
      error: "HTTP 500 Internal Server Error",
      source: "error",
      sourcesDetail: { quotes: "error" },
      refresh: vi.fn(),
    });

    renderQuotes();
    expect(
      screen.getByText(/Datele ofertelor nu au putut fi încărcate din backend/i)
    ).toBeInTheDocument();
  });
});
