/**
 * BUILD 15 — Tests for QuotePdfPanel component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import QuotePdfPanel from "./QuotePdfPanel";

// Mock the API module
vi.mock("@/api/quotePdf", () => ({
  generateQuotePdf: vi.fn(),
  downloadLatestPdf: vi.fn(),
  downloadArchivedPdf: vi.fn(),
  getQuotePdfArchive: vi.fn(),
}));

import {
  generateQuotePdf,
  downloadLatestPdf,
  getQuotePdfArchive,
} from "@/api/quotePdf";

const mockGenerateQuotePdf = vi.mocked(generateQuotePdf);
const mockDownloadLatestPdf = vi.mocked(downloadLatestPdf);
const mockGetQuotePdfArchive = vi.mocked(getQuotePdfArchive);

describe("QuotePdfPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetQuotePdfArchive.mockResolvedValue([]);
  });

  it("renders generate button", async () => {
    render(
      <QuotePdfPanel quoteDbId={1} quoteCode="QT-001" visible={true} />
    );
    await waitFor(() => {
      expect(screen.getByText("Generează PDF")).toBeInTheDocument();
    });
  });

  it("shows no-pdf state when archive is empty", async () => {
    mockGetQuotePdfArchive.mockResolvedValue([]);
    render(
      <QuotePdfPanel quoteDbId={1} quoteCode="QT-001" visible={true} />
    );
    await waitFor(() => {
      expect(screen.getByText("Nu există PDF generat")).toBeInTheDocument();
    });
  });

  it("shows pdf-available state when archive has records", async () => {
    mockGetQuotePdfArchive.mockResolvedValue([
      {
        id: 1,
        quote_id: 1,
        quote_code: "QT-001",
        quote_version: 2,
        filename: "oferta_QT-001_v2.pdf",
        file_size_bytes: 5000,
        content_hash: "abc123def456",
        generated_by: "test@test.com",
        created_at: "2025-05-18T10:00:00",
      },
    ]);

    render(
      <QuotePdfPanel quoteDbId={1} quoteCode="QT-001" visible={true} />
    );

    await waitFor(() => {
      expect(screen.getByText(/PDF disponibil/)).toBeInTheDocument();
    });
  });

  it("triggers generate API call on button click", async () => {
    mockGetQuotePdfArchive.mockResolvedValue([]);
    mockGenerateQuotePdf.mockResolvedValue({
      id: 1,
      quote_id: 1,
      quote_code: "QT-001",
      quote_version: 1,
      filename: "oferta.pdf",
      file_size_bytes: 3000,
      content_hash: "hash",
      generated_by: null,
      created_at: "2025-05-18T10:00:00",
    });

    render(
      <QuotePdfPanel quoteDbId={1} quoteCode="QT-001" visible={true} />
    );

    await waitFor(() => {
      expect(screen.getByText("Generează PDF")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Generează PDF"));

    await waitFor(() => {
      expect(mockGenerateQuotePdf).toHaveBeenCalledWith(1);
    });
  });

  it("triggers download on download button click", async () => {
    mockGetQuotePdfArchive.mockResolvedValue([
      {
        id: 1,
        quote_id: 1,
        quote_code: "QT-001",
        quote_version: 1,
        filename: "oferta.pdf",
        file_size_bytes: 3000,
        content_hash: "hash",
        generated_by: null,
        created_at: "2025-05-18T10:00:00",
      },
    ]);
    mockDownloadLatestPdf.mockResolvedValue(undefined);

    render(
      <QuotePdfPanel quoteDbId={1} quoteCode="QT-001" visible={true} />
    );

    // Wait for archive to load and PDF available state to render
    await waitFor(() => {
      expect(screen.getByText(/PDF disponibil/)).toBeInTheDocument();
    });

    const downloadBtn = screen.getByText("Descarcă");
    expect(downloadBtn).not.toBeDisabled();
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(mockDownloadLatestPdf).toHaveBeenCalledWith(1);
    });
  });

  it("renders nothing when not visible", () => {
    const { container } = render(
      <QuotePdfPanel quoteDbId={1} quoteCode="QT-001" visible={false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when quoteDbId is null", () => {
    const { container } = render(
      <QuotePdfPanel quoteDbId={null} quoteCode="QT-001" visible={true} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("shows archive list when toggle is clicked", async () => {
    mockGetQuotePdfArchive.mockResolvedValue([
      {
        id: 1,
        quote_id: 1,
        quote_code: "QT-001",
        quote_version: 1,
        filename: "v1.pdf",
        file_size_bytes: 2000,
        content_hash: "aaa",
        generated_by: null,
        created_at: "2025-05-17T10:00:00",
      },
      {
        id: 2,
        quote_id: 1,
        quote_code: "QT-001",
        quote_version: 2,
        filename: "v2.pdf",
        file_size_bytes: 3000,
        content_hash: "bbb",
        generated_by: null,
        created_at: "2025-05-18T10:00:00",
      },
    ]);

    render(
      <QuotePdfPanel quoteDbId={1} quoteCode="QT-001" visible={true} />
    );

    await waitFor(() => {
      expect(screen.getByText(/Arată istoric/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Arată istoric/));

    await waitFor(() => {
      expect(screen.getByText(/2 versiuni/)).toBeInTheDocument();
    });
  });

  it("shows error message on generation failure", async () => {
    mockGetQuotePdfArchive.mockResolvedValue([]);
    mockGenerateQuotePdf.mockRejectedValue(new Error("Server error"));

    render(
      <QuotePdfPanel quoteDbId={1} quoteCode="QT-001" visible={true} />
    );

    await waitFor(() => {
      expect(screen.getByText("Generează PDF")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Generează PDF"));

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });
  });
});