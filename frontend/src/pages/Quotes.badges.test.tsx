import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Quotes from "./Quotes";
import type { Quote } from "@/lib/mockData";

const mockNavigate = vi.fn();
const mockUseBackendData = vi.fn();

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

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
  componentBreakdown: [
    {
      component_id: "comp-1",
      name: "Litere volumetrice",
      material_cost: 500,
      operation_cost: 428.01,
      total_component_cost: 928.01,
    },
  ],
};

function renderQuotes(
  initialEntry = "/quotes",
  backendState: {
    quotes: Quote[];
    source: "db" | "mixed" | "mock" | "empty" | "error";
    sourcesDetail?: Record<string, string>;
  },
) {
  mockUseBackendData.mockReturnValue({
    quotes: backendState.quotes,
    loading: false,
    error: null,
    source: backendState.source,
    sourcesDetail: backendState.sourcesDetail ?? {},
    refresh: vi.fn(),
  });

  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/quotes/:quoteId?" element={<Quotes />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Quotes design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders SourceBadge using sourcesDetail.quotes over aggregate source", () => {
    renderQuotes("/quotes", {
      quotes: [pricedQuote],
      source: "mixed",
      sourcesDetail: { quotes: "db", orders: "empty" },
    });

    const badge = screen.getByText("Live DB");
    expect(badge).toHaveAttribute("data-source", "db");
  });

  it("shows Live DB (gol) when quotes source is empty", () => {
    renderQuotes("/quotes", {
      quotes: [],
      source: "empty",
      sourcesDetail: { quotes: "empty" },
    });

    expect(screen.getByText("Live DB (gol)")).toHaveAttribute("data-source", "empty");
    expect(screen.queryByText("Mock Data")).not.toBeInTheDocument();
  });

  it("shows Mock Data when quotes source is mock", () => {
    renderQuotes("/quotes", {
      quotes: [pricedQuote],
      source: "mock",
      sourcesDetail: { quotes: "mock" },
    });

    expect(screen.getByText("Mock Data")).toHaveAttribute("data-source", "mock");
  });

  it("renders quote list status badge with design-system domain and preserved label", () => {
    renderQuotes("/quotes", {
      quotes: [pricedQuote],
      source: "db",
      sourcesDetail: { quotes: "db" },
    });

    const badge = screen.getByText("Priced");
    expect(badge).toHaveAttribute("data-status-domain", "quote");
    expect(badge).toHaveAttribute("data-status", "priced");
    expect(badge).toHaveAttribute("data-status-tone", "violet");
  });

  it("renders detail status badge with design-system on selected quote", () => {
    renderQuotes(`/quotes/${pricedQuote.id}`, {
      quotes: [pricedQuote],
      source: "db",
      sourcesDetail: { quotes: "db" },
    });

    const detailBadge = within(screen.getByTestId("quote-readiness-state")).getByText(
      "Priced",
    );
    expect(detailBadge).toHaveAttribute("data-status-domain", "quote");
    expect(detailBadge).toHaveAttribute("data-status-tone", "violet");
  });

  it("keeps commercial actions enabled when quotes source is db but aggregate is mixed", async () => {
    renderQuotes(`/quotes/${pricedQuote.id}`, {
      quotes: [pricedQuote],
      source: "mixed",
      sourcesDetail: {
        quotes: "db",
        orders: "empty",
      },
    });

    expect(await screen.findByTestId("quote-convert-action")).not.toBeDisabled();
    expect(
      screen.queryByText(/Acțiunile comerciale sunt blocate: necesită contract backend live/i),
    ).not.toBeInTheDocument();
  });

  it("shows disabled commercial reason when quotes source is not db", async () => {
    renderQuotes(`/quotes/${pricedQuote.id}`, {
      quotes: [pricedQuote],
      source: "mixed",
      sourcesDetail: { quotes: "empty" },
    });

    expect(await screen.findByTestId("quote-convert-action")).toBeDisabled();
    expect(
      screen.getByText(/Acțiunile comerciale sunt blocate: necesită contract backend live/i),
    ).toBeInTheDocument();
  });

  it("preserves totals and component breakdown display", async () => {
    renderQuotes(`/quotes/${pricedQuote.id}`, {
      quotes: [pricedQuote],
      source: "db",
      sourcesDetail: { quotes: "db" },
    });

    expect(await screen.findByText("Breakdown pe componente")).toBeInTheDocument();
    expect(screen.getByText("Litere volumetrice")).toBeInTheDocument();
    expect(screen.getAllByText(/1\.104,33/).length).toBeGreaterThan(0);
  });

  it("does not show false aggregate-source warning on live quotes fixture", async () => {
    renderQuotes(`/quotes/${pricedQuote.id}`, {
      quotes: [pricedQuote],
      source: "mixed",
      sourcesDetail: {
        quotes: "db",
        orders: "empty",
        intakes: "db",
      },
    });

    await screen.findByTestId("quote-convert-action");
    expect(screen.queryByText(/^Mixed Source$/)).not.toBeInTheDocument();
    expect(screen.getByText("Live DB")).toHaveAttribute("data-source", "db");
  });
});
