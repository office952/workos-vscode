import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import QuoteCommercialDocument from "./QuoteCommercialDocument";

vi.mock("@/api/quoteDocuments", () => ({
  getQuoteCommercialDocument: vi.fn(),
  downloadQuoteDocument: vi.fn(),
}));

import { getQuoteCommercialDocument } from "@/api/quoteDocuments";

const mockGetDoc = vi.mocked(getQuoteCommercialDocument);

const eurDocument = {
  quote_id: 26,
  quote_code: "Q-1781160194",
  status: "priced",
  version: 1,
  client: { name: "Client EUR" },
  commercial: {
    currency: "EUR",
    tva_percent: 19,
    validity_days: 15,
    payment_terms: "Avans",
    delivery_terms: "Livrare",
    warranty_terms: "Garanție",
  },
  product_summary: { product_name: "Litere", externalized: false },
  product_text: {
    client_title: "Litere volumetrice luminoase",
    short_description: "Litere volumetrice luminoase realizate conform configurației aprobate.",
  },
  line_items: [
    {
      description: "Față litere",
      quantity: 1,
      unit_price: 650,
      total: 650,
      type: "component",
    },
  ],
  totals: {
    subtotal: 1103.64,
    discount: 0,
    discount_pct: 0,
    total_before_vat: 1103.64,
    tva: 209.69,
    grand_total: 1103.64,
    margin_pct: 30,
    currency: "EUR",
  },
  readiness: { source: "snapshot", overall_status: "ready", warnings: [], blockers: [] },
  document: {
    title: "Ofertă",
    sections: [],
    generated_at: "2026-06-11T10:00:00",
    source: "backend",
    format_version: "1.0",
  },
  metadata: { created_at: "2026-06-11T10:00:00", valid_until: "2026-07-01" },
};

describe("QuoteCommercialDocument currency display", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetDoc.mockResolvedValue(eurDocument as never);
  });

  it("shows EUR in Ofertă pentru client header total", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByText(/1\.103,64\s*EUR/)).toBeInTheDocument();
    });
    expect(screen.queryByText(/1\.103,64\s*RON/i)).not.toBeInTheDocument();
  });

  it("shows EUR in Detaliere preț when preview expanded", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByText("Ofertă pentru client")).toBeInTheDocument();
    });

    screen.getByText("Previzualizare").click();

    await waitFor(() => {
      expect(screen.getByText("Detaliere preț")).toBeInTheDocument();
      expect(screen.getAllByText(/EUR/).length).toBeGreaterThan(0);
    });
    expect(screen.queryByText(/RON/)).not.toBeInTheDocument();
  });
});

const alignedEurDocument = {
  ...eurDocument,
  commercial: {
    ...eurDocument.commercial,
    validity_display: "15 zile de la emitere",
  },
  line_items: [
    {
      description: "Litere volumetrice luminoase conform specificațiilor",
      quantity: 1,
      unit_price: 1103.64,
      total: 1103.64,
      type: "commercial_summary",
    },
  ],
  metadata: { created_at: "2026-06-11T10:00:00", valid_until: null },
};

describe("QuoteCommercialDocument client-facing consistency", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetDoc.mockResolvedValue(alignedEurDocument as never);
  });

  it("line total in preview equals subtotal without VAT", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByText("Ofertă pentru client")).toBeInTheDocument();
    });

    screen.getByText("Previzualizare").click();

    await waitFor(() => {
      expect(screen.getByText("Litere volumetrice luminoase conform specificațiilor")).toBeInTheDocument();
      expect(screen.getAllByText(/1\.103,64\s*EUR/).length).toBeGreaterThan(0);
    });
  });

  it("does not show până la em-dash when valid_until missing", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByText(/15 zile de la emitere/)).toBeInTheDocument();
    });
    expect(screen.queryByText(/până la —/)).not.toBeInTheDocument();
  });

  it("does not show CNC/laser in volumetric preview", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByText("Ofertă pentru client")).toBeInTheDocument();
    });

    screen.getByText("Previzualizare").click();

    await waitFor(() => {
      expect(screen.getByText(/Litere volumetrice luminoase/)).toBeInTheDocument();
    });
    expect(screen.queryByText(/CNC/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\blaser\b/i)).not.toBeInTheDocument();
  });
});

describe("QuoteCommercialDocument visual output", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetDoc.mockResolvedValue(alignedEurDocument as never);
  });

  it("renders without crash and opens client-facing preview", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByTestId("quote-commercial-document-panel")).toBeInTheDocument();
    });

    screen.getByTestId("commercial-document-preview-toggle").click();

    await waitFor(() => {
      expect(screen.getByTestId("commercial-document-preview")).toBeInTheDocument();
    });
  });

  it("shows document header with quote code, client and issue date in preview", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByText("Ofertă pentru client")).toBeInTheDocument();
    });

    screen.getByTestId("commercial-document-preview-toggle").click();

    await waitFor(() => {
      expect(screen.getByTestId("commercial-document-quote-code")).toHaveTextContent("Q-1781160194");
      expect(screen.getByTestId("commercial-document-client-block")).toHaveTextContent("Client EUR");
      expect(screen.getByTestId("commercial-document-issue-date")).toHaveTextContent(/2026/i);
    });
  });

  it("keeps financial summary values unchanged in preview", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByText("Ofertă pentru client")).toBeInTheDocument();
    });

    screen.getByTestId("commercial-document-preview-toggle").click();

    await waitFor(() => {
      expect(screen.getByTestId("commercial-document-financial-summary")).toBeInTheDocument();
    });

    const summary = screen.getByTestId("commercial-document-financial-summary");
    expect(summary).toHaveTextContent(/1\.103,64\s*EUR/);
    expect(screen.getByTestId("commercial-document-tva")).toHaveTextContent(/209,69\s*EUR/);
    expect(screen.getByTestId("commercial-document-grand-total")).toHaveTextContent(/1\.103,64\s*EUR/);
    expect(summary).toHaveTextContent(/TVA \(19%\)/);
  });

  it("shows line items and does not expose structure/layer_N or false 0 EUR", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByText("Ofertă pentru client")).toBeInTheDocument();
    });

    screen.getByTestId("commercial-document-preview-toggle").click();

    await waitFor(() => {
      expect(screen.getByTestId("commercial-document-line-item")).toBeInTheDocument();
    });

    expect(screen.queryByText(/structure\/layer/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/0,00\s*EUR/)).not.toBeInTheDocument();
  });

  it("keeps readiness warnings and blockers visible in preview", async () => {
    mockGetDoc.mockResolvedValue({
      ...alignedEurDocument,
      readiness: {
        source: "snapshot",
        overall_status: "blocked",
        warnings: ["Lipsește snapshot output"],
        blockers: ["Breakdown incomplet"],
      },
    } as never);

    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByText("Ofertă pentru client")).toBeInTheDocument();
    });

    screen.getByTestId("commercial-document-preview-toggle").click();

    await waitFor(() => {
      expect(screen.getByTestId("commercial-document-readiness-notes")).toBeInTheDocument();
    });

    expect(screen.getByText(/Warning: Lipsește snapshot output/)).toBeInTheDocument();
    expect(screen.getByText(/Blocker: Breakdown incomplet/)).toBeInTheDocument();
  });

  it("uses design-system StatusBadge in operator chrome", async () => {
    render(<QuoteCommercialDocument quoteDbId={26} quoteCode="Q-1781160194" visible />);

    await waitFor(() => {
      expect(screen.getByTestId("commercial-document-operator-status")).toBeInTheDocument();
    });

    const badge = screen.getByTestId("commercial-document-operator-status").querySelector("[data-status-domain]");
    expect(badge).toHaveAttribute("data-status-domain", "quote");
    expect(badge).toHaveAttribute("data-status", "priced");
  });
});
