import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
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

vi.mock("@/lib/dataStore", () => ({
  updateQuoteStatus: vi.fn(),
  createOrderFromQuote: vi.fn(),
}));

const readyQuote: Quote = {
  id: "QT-READY-001",
  client: "Ready Co",
  contactPerson: "Op",
  assignedTo: "Operator",
  status: "priced",
  version: 1,
  createdAt: "2026-06-01T00:00:00Z",
  validUntil: "2026-06-30",
  subtotal: 1000,
  discount: 0,
  discountPct: 0,
  totalBeforeVAT: 1000,
  vat: 190,
  grandTotal: 1190,
  marginPct: 30,
  lineItems: [],
  notes: "",
  intakeId: "WI-READY-001",
  volumetricReadiness: {
    templateCode: "TPL-VOLUMETRIC-LETTERS",
    quoteGate: { can_create_commercial_quote: true, classified: {} },
  },
};

const ackQuote: Quote = {
  ...readyQuote,
  id: "QT-ACK-001",
  volumetricReadiness: {
    templateCode: "TPL-VOLUMETRIC-LETTERS",
    quoteGate: {
      can_create_commercial_quote: true,
      requires_acknowledgement: true,
      classified: { acknowledgement_pending: ["operations_missing"] },
    },
  },
};

const plainQuote: Quote = {
  ...readyQuote,
  id: "QT-PLAIN-001",
  volumetricReadiness: undefined,
};

describe("Quotes list readiness chips", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Ready chip on volumetric list card", async () => {
    mockUseBackendData.mockReturnValue({
      quotes: [readyQuote],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    render(
      <MemoryRouter initialEntries={["/quotes"]}>
        <Routes>
          <Route path="/quotes" element={<Quotes />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByTestId("quote-readiness-chip-QT-READY-001")).toHaveTextContent("Ready");
    });
  });

  it("shows Requires acknowledgement chip", async () => {
    mockUseBackendData.mockReturnValue({
      quotes: [ackQuote],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    render(
      <MemoryRouter initialEntries={["/quotes"]}>
        <Routes>
          <Route path="/quotes" element={<Quotes />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByTestId("quote-readiness-chip-QT-ACK-001")).toHaveTextContent(
        "Requires acknowledgement"
      );
    });
  });

  it("omits chip when quote has no volumetric quote_gate", async () => {
    mockUseBackendData.mockReturnValue({
      quotes: [plainQuote],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    render(
      <MemoryRouter initialEntries={["/quotes"]}>
        <Routes>
          <Route path="/quotes" element={<Quotes />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("QT-PLAIN-001")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("quote-readiness-chip-QT-PLAIN-001")).not.toBeInTheDocument();
  });
});
