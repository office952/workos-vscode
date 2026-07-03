import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import QuoteSendDialog from "./QuoteSendDialog";
import type { Quote } from "@/lib/mockData";
import { QUOTE_SEND_ASSISTED_NOTICE, QUOTE_SEND_SUCCESS_MESSAGE } from "@/lib/quoteSendLog";

const mockPostQuoteSendLog = vi.fn();

const mockGenerateQuotePdf = vi.fn();
const mockDownloadLatestPdf = vi.fn();

vi.mock("@/api/quotePdf", () => ({
  generateQuotePdf: (...args: unknown[]) => mockGenerateQuotePdf(...args),
  downloadLatestPdf: (...args: unknown[]) => mockDownloadLatestPdf(...args),
}));

vi.mock("@/lib/quotePdfGenerator", () => ({
  generateQuotePDF: vi.fn().mockReturnValue({ url: "blob:test", filename: "q.pdf" }),
  buildMailtoLink: vi.fn().mockReturnValue("mailto:test@example.com"),
  buildWhatsAppLink: vi.fn().mockReturnValue("https://wa.me/"),
  buildQuoteSummaryText: vi.fn().mockReturnValue("summary"),
}));

vi.mock("@/api/quotes", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/quotes")>();
  return {
    ...actual,
    postQuoteSendLog: (...args: unknown[]) => mockPostQuoteSendLog(...args),
  };
});

const quote: Quote = {
  id: "Q-SEND-001",
  dbId: 10,
  intakeId: "",
  client: "Client SRL",
  contactPerson: "Ana Pop",
  assignedTo: "Op",
  status: "priced",
  version: 1,
  createdAt: "2026-06-01T00:00:00Z",
  validUntil: "2026-06-30",
  subtotal: 500,
  discount: 0,
  discountPct: 0,
  totalBeforeVAT: 500,
  vat: 95,
  grandTotal: 595,
  marginPct: 25,
  lineItems: [{ description: "Litere", productCode: "LV", quantity: 1, unitPrice: 500, unitCost: 400, total: 500 }],
  notes: "",
};

describe("QuoteSendDialog assisted send clarity", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGenerateQuotePdf.mockResolvedValue({ id: 1, filename: "oferta.pdf" });
    mockDownloadLatestPdf.mockResolvedValue(undefined);
    mockPostQuoteSendLog.mockResolvedValue({
      quote_id: 10,
      status: "sent",
      quote_version: 1,
      sent_at: "2026-06-08T12:00:00Z",
      status_changed: true,
      log_entry: { channel: "email_manual", sent_at: "2026-06-08T12:00:00Z", quote_version: 1 },
    });
  });

  it("shows assisted send notice and status marking copy for priced quote", () => {
    render(
      <QuoteSendDialog quote={quote} open onClose={() => undefined} />
    );

    expect(screen.getByTestId("quote-send-assisted-notice")).toHaveTextContent(
      /Trimitere asistată|nu trimite email automat/i
    );
    expect(screen.getByTestId("quote-send-assisted-notice")).toHaveTextContent(
      QUOTE_SEND_ASSISTED_NOTICE
    );
    expect(screen.getByTestId("quote-send-status-notice")).toHaveTextContent(/trimisă/i);
  });

  it("does not show status marking copy when quote already sent", () => {
    render(
      <QuoteSendDialog
        quote={{ ...quote, status: "sent" }}
        open
        onClose={() => undefined}
      />
    );

    expect(screen.getByTestId("quote-send-assisted-notice")).toBeInTheDocument();
    expect(screen.queryByTestId("quote-send-status-notice")).not.toBeInTheDocument();
  });

  it("requires channel and submits to send-log endpoint", async () => {
    const onRegistered = vi.fn().mockResolvedValue(undefined);
    render(
      <QuoteSendDialog
        quote={quote}
        open
        onClose={() => undefined}
        onRegistered={onRegistered}
      />
    );

    fireEvent.change(screen.getByTestId("quote-send-recipient-input"), {
      target: { value: "client@example.com" },
    });
    fireEvent.click(screen.getByTestId("quote-send-confirm-action"));

    await waitFor(() => {
      expect(mockPostQuoteSendLog).toHaveBeenCalledWith(
        10,
        expect.objectContaining({
          channel: "email_manual",
          recipient: "client@example.com",
        })
      );
    });
    expect(onRegistered).toHaveBeenCalled();
    expect(await screen.findByTestId("quote-send-success-message")).toHaveTextContent(
      QUOTE_SEND_SUCCESS_MESSAGE
    );
  });

  it("uses backend PDF path when quote has dbId", async () => {
    render(<QuoteSendDialog quote={quote} open onClose={() => undefined} />);

    fireEvent.click(screen.getByText("PDF"));

    await waitFor(() => {
      expect(mockGenerateQuotePdf).toHaveBeenCalledWith(10);
      expect(mockDownloadLatestPdf).toHaveBeenCalledWith(10);
    });
  });

  it("shows EUR total when quote currency is EUR", () => {
    render(
      <QuoteSendDialog
        quote={{ ...quote, currency: "EUR", grandTotal: 768 }}
        open
        onClose={() => undefined}
      />
    );

    expect(screen.getByText(/768.*EUR/)).toBeInTheDocument();
    expect(screen.queryByText(/768.*RON/i)).not.toBeInTheDocument();
  });

  it("shows error without optimistic success on API failure", async () => {
    mockPostQuoteSendLog.mockRejectedValue(new Error("Backend indisponibil"));
    render(<QuoteSendDialog quote={quote} open onClose={() => undefined} />);

    fireEvent.click(screen.getByTestId("quote-send-confirm-action"));

    expect(await screen.findByTestId("quote-send-submit-error")).toHaveTextContent(
      /Backend indisponibil/i
    );
    expect(screen.queryByTestId("quote-send-success")).not.toBeInTheDocument();
  });
});
