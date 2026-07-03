/**
 * BUILD 15 — Quote PDF API adapter.
 *
 * Functions:
 *   generateQuotePdf(quoteId) — trigger PDF generation
 *   downloadLatestPdf(quoteId) — download most recent PDF
 *   getQuotePdfArchive(quoteId) — list all generated PDFs
 *   downloadArchivedPdf(quoteId, archiveId) — download specific version
 *
 * Rules:
 *   - No silent mock fallback.
 *   - Throws on backend error.
 *   - Uses additive /pdf/ route (does NOT touch /commercial-document).
 */

import { getAPIBaseURL } from "@/lib/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface PdfArchiveRecord {
  id: number;
  quote_id: number;
  quote_code: string;
  quote_version: number;
  filename: string;
  file_size_bytes: number | null;
  content_hash: string | null;
  generated_by: string | null;
  created_at: string | null;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/**
 * Generate a new PDF for the given quote.
 * Returns the archive record on success.
 */
export async function generateQuotePdf(
  quoteId: number
): Promise<PdfArchiveRecord> {
  const base = getAPIBaseURL();
  const url = `${base}/api/v1/entities/quotes/${quoteId}/pdf/generate`;

  const res = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(
      `Failed to generate PDF for quote ${quoteId}: ${res.status} — ${detail}`
    );
  }

  return res.json();
}

/**
 * Download the most recent PDF for a quote.
 * Triggers a browser file download.
 */
export async function downloadLatestPdf(quoteId: number): Promise<void> {
  const base = getAPIBaseURL();
  const url = `${base}/api/v1/entities/quotes/${quoteId}/pdf/latest`;

  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(
      `Failed to download PDF for quote ${quoteId}: ${res.status} — ${detail}`
    );
  }

  const blob = await res.blob();
  const downloadUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;

  // Extract filename from Content-Disposition header if available
  const disposition = res.headers.get("Content-Disposition");
  const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
  a.download = filenameMatch?.[1] || `oferta_${quoteId}.pdf`;

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(downloadUrl);
}

/**
 * Get the list of all generated PDFs for a quote (archive history).
 */
export async function getQuotePdfArchive(
  quoteId: number
): Promise<PdfArchiveRecord[]> {
  const base = getAPIBaseURL();
  const url = `${base}/api/v1/entities/quotes/${quoteId}/pdf/archive`;

  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(
      `Failed to fetch PDF archive for quote ${quoteId}: ${res.status} — ${detail}`
    );
  }

  return res.json();
}

/**
 * Download a specific archived PDF by archive ID.
 * Triggers a browser file download.
 */
export async function downloadArchivedPdf(
  quoteId: number,
  archiveId: number
): Promise<void> {
  const base = getAPIBaseURL();
  const url = `${base}/api/v1/entities/quotes/${quoteId}/pdf/${archiveId}/download`;

  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(
      `Failed to download archived PDF ${archiveId}: ${res.status} — ${detail}`
    );
  }

  const blob = await res.blob();
  const downloadUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;

  const disposition = res.headers.get("Content-Disposition");
  const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
  a.download = filenameMatch?.[1] || `oferta_${quoteId}_${archiveId}.pdf`;

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(downloadUrl);
}