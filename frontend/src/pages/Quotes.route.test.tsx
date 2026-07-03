import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  default: ({ open }: { open: boolean }) =>
    open ? <div data-testid="quote-wizard">wizard</div> : null,
}));

vi.mock("@/lib/dataStore", () => ({
  updateQuoteStatus: vi.fn(),
  createOrderFromQuote: vi.fn(),
}));

const sampleQuote: Quote = {
  id: "QT-2245",
  client: "MOL",
  contactPerson: "Radu",
  assignedTo: "Operator",
  status: "rejected",
  version: 1,
  createdAt: "2026-04-01T00:00:00Z",
  validUntil: "2026-04-20",
  subtotal: 1000,
  discount: 0,
  discountPct: 0,
  totalBeforeVAT: 1000,
  vat: 190,
  grandTotal: 1190,
  marginPct: 30,
  lineItems: [],
  notes: "",
  intakeId: "WI-3320",
};

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/quotes/:quoteId" element={<Quotes />} />
        <Route path="/quotes" element={<Quotes />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Quotes direct route", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBackendData.mockReturnValue({
      quotes: [sampleQuote],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
  });

  it("auto-selects quote from /quotes/:quoteId", async () => {
    renderAt("/quotes/QT-2245");
    await waitFor(() => {
      expect(screen.getAllByText("QT-2245").length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText("MOL").length).toBeGreaterThan(0);
  });

  it("shows not found for unknown quote id", async () => {
    renderAt("/quotes/QT-MISSING");
    await waitFor(() => {
      expect(screen.getByTestId("quote-not-found")).toBeInTheDocument();
    });
  });

  it("shows terminal policy for rejected quotes", async () => {
    renderAt("/quotes/QT-2245");
    await waitFor(() => {
      expect(screen.getByTestId("quote-terminal-policy")).toBeInTheDocument();
    });
    expect(screen.getByTestId("quote-terminal-policy")).toHaveTextContent(
      /respinsă/i
    );
    expect(
      screen.queryByRole("button", { name: /Deschide trimitere asistată/i })
    ).not.toBeInTheDocument();
  });

  it("/quotes list still works without id", () => {
    renderAt("/quotes");
    expect(screen.getByText(/Selectează o ofertă/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText("QT-2245"));
    expect(screen.getAllByText("QT-2245").length).toBeGreaterThan(1);
  });
});
