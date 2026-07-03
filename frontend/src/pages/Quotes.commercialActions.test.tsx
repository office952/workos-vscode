import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Quotes from "./Quotes";
import type { Quote } from "@/lib/mockData";

const mockNavigate = vi.fn();
const mockRefresh = vi.fn();

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
  default: () => null,
}));

vi.mock("@/components/workos/QuoteRevisionDialog", () => ({
  default: () => null,
}));

vi.mock("@/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel", () => ({
  default: ({ workspaceId, quoteId, intakeCode }: { workspaceId: string; quoteId: number | null; intakeCode: string | null }) => (
    <div data-testid="intake-v6-commercial-spine-mock">
      {workspaceId}|{quoteId}|{intakeCode}
    </div>
  ),
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
  discountPct: 12,
  totalBeforeVAT: 1000,
  vat: 190,
  grandTotal: 1190,
  marginPct: 30,
  lineItems: [],
  notes: "",
};

const linkedV6Quote: Quote = {
  ...linkedQuote,
  id: "Q-V6-IV6-41401270-7151-419c-b520-dec258409593-1782492520",
  dbId: 11,
  intakeId: "IV6-41401270-7151-419c-b520-dec258409593",
  status: "draft",
};

function renderQuoteDetail(quote: Quote) {
  mockUseBackendData.mockReturnValue({
    quotes: [quote],
    loading: false,
    error: null,
    source: "db",
    refresh: mockRefresh,
  });

  return render(
    <MemoryRouter initialEntries={[`/quotes/${quote.id}`]}>
      <Routes>
        <Route path="/quotes/:quoteId?" element={<Quotes />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Quotes commercial action panel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRefresh.mockResolvedValue(undefined);
  });

  it("shows commercial panel with margin, discount, version and intake link", async () => {
    renderQuoteDetail(linkedQuote);

    expect(await screen.findByTestId("quote-commercial-action-panel")).toBeInTheDocument();
    expect(screen.getByTestId("quote-commercial-margin")).toHaveTextContent("30%");
    expect(screen.getByTestId("quote-commercial-discount")).toHaveTextContent("12%");
    expect(screen.getByTestId("quote-commercial-version")).toHaveTextContent("v1");
    expect(screen.getByTestId("quote-commercial-intake-link")).toHaveAttribute(
      "href",
      "/intake-v6/WI-E2E-LINK-001/operator"
    );
    expect(screen.getByTestId("quote-revision-mechanism-notice")).toHaveTextContent(/recalculează/i);
  });

  it("priced quote shows revision action and assisted send", async () => {
    renderQuoteDetail(linkedQuote);

    expect(await screen.findByTestId("quote-revision-action")).toBeInTheDocument();
    expect(screen.getByTestId("quote-revision-open-action")).toBeInTheDocument();
    expect(screen.getByTestId("quote-assisted-send-action")).toBeInTheDocument();
    expect(screen.getByTestId("quote-convert-action")).toBeInTheDocument();
    expect(screen.getByTestId("quote-commercial-next-action")).toHaveTextContent(/trimite/i);
  });

  it("accepted quote hides revision and shows convert guidance", async () => {
    renderQuoteDetail({ ...linkedQuote, status: "accepted" });

    expect(await screen.findByTestId("quote-convert-action")).toBeInTheDocument();
    expect(screen.queryByTestId("quote-revision-action")).not.toBeInTheDocument();
    expect(screen.queryByTestId("quote-accept-action")).not.toBeInTheDocument();
    expect(screen.getByTestId("quote-commercial-next-action")).toHaveTextContent(/convertește/i);
  });

  it("rejected quote hides revision and convert", async () => {
    renderQuoteDetail({ ...linkedQuote, status: "rejected" });

    expect(await screen.findByTestId("quote-commercial-action-panel")).toBeInTheDocument();
    expect(screen.queryByTestId("quote-revision-action")).not.toBeInTheDocument();
    expect(screen.queryByTestId("quote-convert-action")).not.toBeInTheDocument();
    expect(screen.getByTestId("quote-commercial-next-action")).toHaveTextContent(/terminal/i);
    expect(screen.getByTestId("quote-terminal-policy")).toBeInTheDocument();
  });

  it("sent quote shows accept, reject, expire and revision actions", async () => {
    renderQuoteDetail({ ...linkedQuote, status: "sent" });

    expect(await screen.findByTestId("quote-accept-action")).toBeInTheDocument();
    expect(screen.getByTestId("quote-accept-action")).toHaveTextContent(/acceptată intern/i);
    expect(screen.getByTestId("quote-reject-action")).toBeInTheDocument();
    expect(screen.getByTestId("quote-expire-action")).toBeInTheDocument();
    expect(screen.getByTestId("quote-revision-action")).toBeInTheDocument();
    expect(screen.queryByTestId("quote-convert-action")).not.toBeInTheDocument();
    expect(screen.getByTestId("quote-acceptance-clarity-notice")).toHaveTextContent(
      /nu trimite un link clientului/i
    );
    expect(screen.getByTestId("quote-acceptance-clarity-notice")).toHaveTextContent(
      /nu creează automat comanda/i
    );
  });

  it("priced quote shows conversion summary and priced convert guidance", async () => {
    renderQuoteDetail(linkedQuote);

    expect(await screen.findByTestId("quote-conversion-summary-panel")).toBeInTheDocument();
    expect(screen.getByTestId("quote-conversion-summary-line")).toHaveTextContent(
      /Q-WI-LINK-001 · v1 · Linkage Client · cerere WI-E2E-LINK-001/
    );
    expect(screen.getByTestId("quote-conversion-active-version")).toHaveTextContent(/v1/);
    expect(screen.getByTestId("quote-priced-convert-guidance")).toHaveTextContent(
      /marchează acceptarea internă/i
    );
    expect(screen.getByTestId("quote-convert-action")).toHaveTextContent(
      /Creează comandă din oferta activă/i
    );
  });

  it("accepted quote shows conversion summary without priced-only guidance", async () => {
    renderQuoteDetail({ ...linkedQuote, status: "accepted" });

    expect(await screen.findByTestId("quote-conversion-summary-panel")).toBeInTheDocument();
    expect(screen.queryByTestId("quote-priced-convert-guidance")).not.toBeInTheDocument();
    expect(screen.getByTestId("quote-convert-action")).toHaveTextContent(
      /Creează comandă din oferta activă/i
    );
  });

  it("expired quote hides conversion summary and convert action", async () => {
    renderQuoteDetail({ ...linkedQuote, status: "expired" });

    expect(await screen.findByTestId("quote-commercial-action-panel")).toBeInTheDocument();
    expect(screen.queryByTestId("quote-conversion-summary-panel")).not.toBeInTheDocument();
    expect(screen.queryByTestId("quote-convert-action")).not.toBeInTheDocument();
  });

  it("shows revision history and send history when present", async () => {
    renderQuoteDetail({
      ...linkedQuote,
      status: "priced",
      version: 3,
      revisionHistory: [
        {
          version: 2,
          archivedAt: "2026-06-02T12:00:00Z",
          discountPct: 5,
          grandTotal: 1130.5,
        },
      ],
      commercialDeliveryLog: [
        {
          channel: "email_manual",
          sent_at: "2026-06-01T10:00:00Z",
          quote_version: 2,
          recipient: "client@example.com",
        },
      ],
    });

    expect(await screen.findByTestId("quote-revision-history-panel")).toBeInTheDocument();
    expect(screen.getByTestId("quote-revision-history-v2")).toHaveTextContent(/v2/);
    expect(screen.getByTestId("quote-send-history-panel")).toBeInTheDocument();
    expect(screen.getByTestId("quote-send-history-latest")).toHaveTextContent(/v2/);
  });

  it("shows the dedicated V6 commercial spine and hides generic commercial actions", async () => {
    renderQuoteDetail(linkedV6Quote);

    expect(await screen.findByTestId("intake-v6-commercial-spine-mock")).toHaveTextContent(
      "41401270-7151-419c-b520-dec258409593|11|IV6-41401270-7151-419c-b520-dec258409593"
    );
    expect(screen.queryByTestId("quote-truth-boundary")).not.toBeInTheDocument();
    expect(screen.queryByTestId("quote-v6-detail-unpriced-total")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-quote-detail-extras")).toBeInTheDocument();
    expect(screen.queryByTestId("quote-commercial-action-panel")).not.toBeInTheDocument();
    expect(screen.queryByTestId("quote-assisted-send-action")).not.toBeInTheDocument();
    expect(screen.queryByTestId("quote-convert-action")).not.toBeInTheDocument();
  });
});
