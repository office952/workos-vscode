import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Quotes from "./Quotes";
import type { Quote } from "@/lib/mockData";
import { createOrderFromQuote } from "@/lib/dataStore";

const mockUseBackendData = vi.fn();
const mockCreateOrderFromQuote = vi.mocked(createOrderFromQuote);

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

vi.mock("@/lib/dataStore", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/dataStore")>();
  return {
    ...actual,
    updateQuoteStatus: vi.fn(),
    createOrderFromQuote: vi.fn(),
  };
});

const ackQuote: Quote = {
  id: "QT-ACK-001",
  dbId: 99,
  client: "Ack Client",
  contactPerson: "Operator",
  assignedTo: "Operator",
  status: "accepted",
  version: 1,
  createdAt: "2026-06-01T00:00:00Z",
  validUntil: "2026-06-30",
  subtotal: 5000,
  discount: 0,
  discountPct: 0,
  totalBeforeVAT: 5000,
  vat: 950,
  grandTotal: 5950,
  marginPct: 25,
  lineItems: [],
  notes: "",
  intakeId: "WI-ACK-001",
  volumetricReadiness: {
    templateCode: "TPL-VOLUMETRIC-LETTERS",
    quoteGate: {
      can_create_commercial_quote: true,
      requires_acknowledgement: true,
      warnings: ["operations_missing"],
      classified: {
        acknowledgement_pending: ["operations_missing"],
        warnings: ["operations_missing"],
      },
    },
  },
};

const blockedQuote: Quote = {
  ...ackQuote,
  id: "QT-BLOCK-001",
  volumetricReadiness: {
    templateCode: "TPL-VOLUMETRIC-LETTERS",
    quoteGate: {
      can_create_commercial_quote: false,
      requires_acknowledgement: false,
      blockers: ["letters_vector_file_required"],
      classified: {
        vector_blockers: ["letters_vector_file_required"],
      },
    },
  },
};

function renderQuotes(quoteId: string) {
  return render(
    <MemoryRouter initialEntries={[`/quotes/${quoteId}`]}>
      <Routes>
        <Route path="/quotes/:quoteId" element={<Quotes />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Quotes volumetric readiness UX", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateOrderFromQuote.mockResolvedValue("ORD-001");
  });

  it("disables convert until acknowledgement when requires_acknowledgement", async () => {
    mockUseBackendData.mockReturnValue({
      quotes: [ackQuote],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderQuotes("QT-ACK-001");
    await waitFor(() => {
      expect(screen.getByTestId("quote-volumetric-readiness")).toBeInTheDocument();
    });

    const convertBtn = screen.getByTestId("quote-convert-action");
    expect(convertBtn).toBeDisabled();
    expect(screen.getByTestId("quote-convert-ack-hint")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("checkbox"));
    expect(convertBtn).not.toBeDisabled();

    fireEvent.click(convertBtn);
    await waitFor(() => {
      expect(mockCreateOrderFromQuote).toHaveBeenCalledWith(
        "QT-ACK-001",
        expect.objectContaining({ acknowledge_readiness_warnings: true })
      );
    });
  });

  it("keeps convert disabled for hard blockers", async () => {
    mockUseBackendData.mockReturnValue({
      quotes: [blockedQuote],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
    renderQuotes("QT-BLOCK-001");
    await waitFor(() => {
      expect(screen.getByTestId("quote-volumetric-readiness-status")).toHaveTextContent(
        "Blocked"
      );
    });

    const convertBtn = screen.getByTestId("quote-convert-action");
    expect(convertBtn).toBeDisabled();
    expect(screen.getByTestId("quote-convert-blocked-hint")).toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });
});
