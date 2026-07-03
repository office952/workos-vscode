import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import QuoteRevisionDialog from "./QuoteRevisionDialog";
import type { Quote } from "@/lib/mockData";
import {
  LEGACY_REVISION_BLOCKED_MESSAGE,
  LEGACY_REVISION_RECOVERY_MESSAGE,
  QUOTE_REVISION_SUCCESS_MESSAGE,
} from "@/lib/quoteRevision";

const mockGetQuote = vi.fn();
const mockPriceExistingQuote = vi.fn();

vi.mock("@/lib/api", () => ({
  getQuote: (...args: unknown[]) => mockGetQuote(...args),
}));

vi.mock("@/api/quotes", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/quotes")>();
  return {
    ...actual,
    priceExistingQuote: (...args: unknown[]) => mockPriceExistingQuote(...args),
  };
});

const quote: Quote = {
  id: "Q-REV-DLG-001",
  dbId: 501,
  intakeId: "WI-REV-LINK",
  client: "Revision Client",
  contactPerson: "Contact",
  assignedTo: "Op",
  status: "sent",
  version: 3,
  createdAt: "2026-06-01T00:00:00Z",
  validUntil: "2026-06-30",
  subtotal: 1000,
  discount: 0,
  discountPct: 8,
  totalBeforeVAT: 1000,
  vat: 190,
  grandTotal: 1190,
  marginPct: 30,
  lineItems: [],
  notes: "",
};

const revisionSourceWrapper = {
  line_items: { status: "priced" },
  revision_source: {
    product_template: { id: 1, template_code: "TPL" },
    user_config: { quantity: 1 },
    pricing: { margin_pct: 30, discount_pct: 8, vat_pct: 19 },
  },
};

function renderDialog(overrides?: Partial<Quote>) {
  return render(
    <MemoryRouter>
      <QuoteRevisionDialog
        quote={{ ...quote, ...overrides }}
        open
        onClose={() => undefined}
        onRevised={() => undefined}
      />
    </MemoryRouter>
  );
}

describe("QuoteRevisionDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetQuote.mockResolvedValue({
      line_items: JSON.stringify(revisionSourceWrapper),
      intake_id: 88,
    });
    mockPriceExistingQuote.mockResolvedValue({
      quote_id: 501,
      quote_version: 4,
      revised: true,
      snapshot: { status: "priced" },
    });
  });

  it("shows current totals, discount, margin and version", async () => {
    renderDialog();

    expect(await screen.findByTestId("quote-revision-current-version")).toHaveTextContent("v3");
    expect(screen.getByTestId("quote-revision-current-discount")).toHaveTextContent("8%");
    expect(screen.getByTestId("quote-revision-current-margin")).toHaveTextContent("30%");
    expect(screen.getByTestId("quote-revision-mechanism-notice")).toHaveTextContent(/recalculează/i);
    expect(screen.getByTestId("quote-revision-resend-notice")).toHaveTextContent(/retrimis/i);
  });

  it("blocks invalid discount in UI", async () => {
    renderDialog();

    await screen.findByTestId("quote-revision-discount-input");
    fireEvent.change(screen.getByTestId("quote-revision-discount-input"), {
      target: { value: "75" },
    });
    expect(screen.getByTestId("quote-revision-discount-error")).toBeInTheDocument();
    expect(screen.getByTestId("quote-revision-submit")).toBeDisabled();
  });

  it("submits embedded source to priceExistingQuote and shows success", async () => {
    const onRevised = vi.fn().mockResolvedValue(undefined);
    render(
      <MemoryRouter>
        <QuoteRevisionDialog
          quote={quote}
          open
          onClose={() => undefined}
          onRevised={onRevised}
        />
      </MemoryRouter>
    );

    await screen.findByTestId("quote-revision-discount-input");
    fireEvent.change(screen.getByTestId("quote-revision-discount-input"), {
      target: { value: "15" },
    });
    fireEvent.click(screen.getByTestId("quote-revision-submit"));

    await waitFor(() => {
      expect(mockPriceExistingQuote).toHaveBeenCalledWith(
        501,
        expect.objectContaining({
          pricing: expect.objectContaining({ discount_pct: 15 }),
          product_template: expect.objectContaining({ id: 1 }),
        })
      );
    });
    expect(onRevised).toHaveBeenCalled();
    expect(await screen.findByTestId("quote-revision-success-message")).toHaveTextContent(
      QUOTE_REVISION_SUCCESS_MESSAGE
    );
  });

  it("accepts IV6 linkage in notes as legacy repricing candidate", async () => {
    mockGetQuote.mockResolvedValue({
      line_items: JSON.stringify([{ description: "Operator workspace V6", quantity: 1 }]),
      notes: JSON.stringify({
        intake_v6_linkage_v1: {
          source_workspace_code: "IV6-DC1B0887",
          quote_input_payload: { width_mm: 5087, height_mm: 600 },
        },
      }),
      intake_id: null,
    });

    renderDialog();
    await screen.findByTestId("quote-revision-discount-input");
    expect(screen.queryByTestId("quote-revision-blocked-message")).not.toBeInTheDocument();
    expect(screen.getByTestId("quote-revision-submit")).not.toBeDisabled();
  });

  it("shows legacy blocked message with intake recovery link", async () => {
    mockGetQuote.mockResolvedValue({
      line_items: JSON.stringify([{ description: "Linie veche", quantity: 1 }]),
      notes: null,
    });
    renderDialog();

    expect(await screen.findByTestId("quote-revision-blocked-message")).toHaveTextContent(
      LEGACY_REVISION_BLOCKED_MESSAGE
    );
    expect(screen.getByTestId("quote-revision-recovery-message")).toHaveTextContent(
      LEGACY_REVISION_RECOVERY_MESSAGE
    );
    expect(screen.getByTestId("quote-revision-intake-recovery-link")).toHaveAttribute(
      "href",
      "/intake-v6/WI-REV-LINK/operator"
    );
    expect(screen.getByTestId("quote-revision-submit")).toBeDisabled();
  });

  it("submits legacy candidate with pricing-only payload", async () => {
    mockGetQuote.mockResolvedValue({
      line_items: JSON.stringify({
        line_items: {
          template_id: 1,
          product_definition: {
            quantity: 2,
            dimensions: { width_mm: 1000, height_mm: 3000, depth_mm: 300 },
          },
          pricing: { margin_pct: 25, discount_pct: 8, vat_pct: 19 },
          cost_result: { total_cost: 80 },
          price: { net: 100, gross: 119 },
        },
      }),
      intake_id: 55,
    });

    renderDialog();
    await screen.findByTestId("quote-revision-discount-input");
    fireEvent.click(screen.getByTestId("quote-revision-submit"));

    await waitFor(() => {
      expect(mockPriceExistingQuote).toHaveBeenCalledWith(
        501,
        expect.objectContaining({
          pricing: expect.objectContaining({ discount_pct: 8 }),
          intake_id: 55,
        })
      );
    });
    expect(mockPriceExistingQuote.mock.calls[0][1].product_template).toBeUndefined();
  });

  it("shows error message when API fails without optimistic update", async () => {
    mockPriceExistingQuote.mockRejectedValue(new Error("Backend indisponibil"));

    renderDialog();
    await screen.findByTestId("quote-revision-discount-input");
    fireEvent.click(screen.getByTestId("quote-revision-submit"));

    expect(await screen.findByTestId("quote-revision-submit-error")).toHaveTextContent(
      /Backend indisponibil/i
    );
    expect(screen.queryByTestId("quote-revision-success")).not.toBeInTheDocument();
  });
});
