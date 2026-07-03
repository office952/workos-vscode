import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Quotes from "./Quotes";
import type { Quote } from "@/lib/mockData";

const mockNavigate = vi.fn();
const mockRefresh = vi.fn();
let latestWizardProps: {
  onOpenCreatedQuote?: (created: { quoteId: number; quoteCode?: string }) => void;
} | null = null;

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

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
  default: (props: {
    open?: boolean;
    onOpenCreatedQuote?: (created: { quoteId: number; quoteCode?: string }) => void;
  }) => {
    latestWizardProps = props;
    if (!props.open) return null;
    return (
      <button
        type="button"
        data-testid="mock-open-created-quote"
        onClick={() =>
          props.onOpenCreatedQuote?.({
            quoteId: 501,
            quoteCode: "Q-WI-LINK-001",
          })
        }
      >
        Mock open created quote
      </button>
    );
  },
}));

vi.mock("@/lib/dataStore", () => ({
  updateQuoteStatus: vi.fn(),
  createOrderFromQuote: vi.fn(),
}));

const linkedQuote: Quote = {
  id: "Q-WI-LINK-001",
  dbId: 501,
  intakeId: "WI-E2E-LINK-001",
  client: "Linkage Client",
  contactPerson: "Linkage Contact",
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
};

describe("Quotes commercial navigation and traceability", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    latestWizardProps = null;
    mockRefresh.mockResolvedValue(undefined);
  });

  it("shows intake code on list card and detail link", async () => {
    mockUseBackendData.mockReturnValue({
      quotes: [linkedQuote],
      loading: false,
      error: null,
      source: "db",
      refresh: mockRefresh,
    });

    render(
      <MemoryRouter initialEntries={["/quotes/Q-WI-LINK-001"]}>
        <Routes>
          <Route path="/quotes/:quoteId?" element={<Quotes />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText(/din cerere WI-E2E-LINK-001/i)).toBeInTheDocument();
    expect(screen.getByTestId("quote-detail-intake-link")).toHaveAttribute(
      "href",
      "/intake-v6/WI-E2E-LINK-001/operator"
    );
  });

  it("filters quotes by intake code via search input", () => {
    mockUseBackendData.mockReturnValue({
      quotes: [
        linkedQuote,
        {
          ...linkedQuote,
          id: "Q-OTHER-002",
          intakeId: "WI-OTHER-002",
          client: "Other Client",
        },
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: mockRefresh,
    });

    render(
      <MemoryRouter initialEntries={["/quotes"]}>
        <Routes>
          <Route path="/quotes/:quoteId?" element={<Quotes />} />
        </Routes>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByTestId("quotes-search-input"), {
      target: { value: "WI-E2E-LINK-001" },
    });

    expect(screen.getByText("Q-WI-LINK-001")).toBeInTheDocument();
    expect(screen.queryByText("Q-OTHER-002")).not.toBeInTheDocument();
  });

  it("navigates to created quote detail when Deschide oferta handoff fires", async () => {
    mockUseBackendData.mockReturnValue({
      quotes: [linkedQuote],
      loading: false,
      error: null,
      source: "db",
      refresh: mockRefresh,
    });

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: "/quotes",
            state: {
              openWizard: true,
              fromIntake: true,
              templateCode: "TPL-VOLUMETRIC-LETTERS",
              intakeRequestId: "WI-E2E-LINK-001",
            },
          },
        ]}
      >
        <Routes>
          <Route path="/quotes/:quoteId?" element={<Quotes />} />
        </Routes>
      </MemoryRouter>
    );

    expect(latestWizardProps?.onOpenCreatedQuote).toBeTypeOf("function");
    fireEvent.click(screen.getByTestId("mock-open-created-quote"));

    await vi.waitFor(() => {
      expect(mockRefresh).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith("/quotes/Q-WI-LINK-001", {
        replace: true,
        state: {},
      });
    });
  });
});
