/**
 * BUILD 15 — Quote PDF Panel Component.
 *
 * Displays PDF generation controls, download button, and archive history.
 * Integrates alongside the existing QuoteCommercialDocument component.
 *
 * Features:
 *   - Generate PDF button (triggers backend generation)
 *   - Download latest PDF button
 *   - Archive list with version history
 *   - Status indicator (no PDF / PDF available)
 *   - Traceability badge (quote code + version)
 */

import { useState, useEffect, useCallback } from "react";
import { FileText, Download, RefreshCw, Clock, Hash } from "lucide-react";
import {
  generateQuotePdf,
  downloadLatestPdf,
  downloadArchivedPdf,
  getQuotePdfArchive,
  PdfArchiveRecord,
} from "@/api/quotePdf";

interface QuotePdfPanelProps {
  quoteDbId: number | null;
  quoteCode: string;
  visible?: boolean;
}

export default function QuotePdfPanel({
  quoteDbId,
  quoteCode,
  visible = true,
}: QuotePdfPanelProps) {
  const [archives, setArchives] = useState<PdfArchiveRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showArchive, setShowArchive] = useState(false);

  const loadArchive = useCallback(async () => {
    if (!quoteDbId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getQuotePdfArchive(quoteDbId);
      setArchives(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la încărcare");
    } finally {
      setLoading(false);
    }
  }, [quoteDbId]);

  useEffect(() => {
    if (visible && quoteDbId) {
      loadArchive();
    }
  }, [visible, quoteDbId, loadArchive]);

  if (!visible || !quoteDbId) return null;

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setSuccess(null);
    try {
      await generateQuotePdf(quoteDbId);
      setSuccess("PDF generat cu succes");
      await loadArchive();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la generare PDF");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadLatest = async () => {
    try {
      setError(null);
      await downloadLatestPdf(quoteDbId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la descărcare");
    }
  };

  const handleDownloadArchived = async (archiveId: number) => {
    try {
      setError(null);
      await downloadArchivedPdf(quoteDbId, archiveId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la descărcare");
    }
  };

  const latest = archives.length > 0 ? archives[0] : null;

  const formatDate = (isoStr: string | null) => {
    if (!isoStr) return "—";
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString("ro-RO", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoStr;
    }
  };

  const formatBytes = (bytes: number | null) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-400" />
          <h3 className="text-[13px] font-semibold text-slate-200">
            Document PDF
          </h3>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">BUILD 15</span>
      </div>

      {/* Status */}
      <div className="mb-3">
        {latest ? (
          <div className="flex items-center gap-2 text-[11px]">
            <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
            <span className="text-green-400">
              PDF disponibil (v{latest.quote_version}, generat{" "}
              {formatDate(latest.created_at)})
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-[11px]">
            <span className="inline-block w-2 h-2 rounded-full bg-slate-500" />
            <span className="text-slate-400">Nu există PDF generat</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 mb-3">
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-50 text-white text-[11px] font-medium rounded transition-colors"
        >
          {generating ? (
            <RefreshCw className="w-3 h-3 animate-spin" />
          ) : (
            <FileText className="w-3 h-3" />
          )}
          {generating ? "Se generează..." : "Generează PDF"}
        </button>

        <button
          onClick={handleDownloadLatest}
          disabled={!latest}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:opacity-50 text-slate-200 text-[11px] font-medium rounded transition-colors"
        >
          <Download className="w-3 h-3" />
          Descarcă
        </button>
      </div>

      {/* Success/Error messages */}
      {success && (
        <div className="mb-2 px-2 py-1 bg-green-900/30 border border-green-700 rounded text-[11px] text-green-400">
          {success}
        </div>
      )}
      {error && (
        <div className="mb-2 px-2 py-1 bg-red-900/30 border border-red-700 rounded text-[11px] text-red-400">
          {error}
        </div>
      )}

      {/* Traceability badge */}
      {latest && (
        <div className="mb-3 flex items-center gap-2 text-[10px] text-slate-500">
          <Hash className="w-3 h-3" />
          <span>
            {latest.quote_code} v{latest.quote_version} •{" "}
            {latest.content_hash?.slice(0, 12)}...
          </span>
        </div>
      )}

      {/* Archive toggle */}
      {archives.length > 0 && (
        <div>
          <button
            onClick={() => setShowArchive(!showArchive)}
            className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-300 transition-colors"
          >
            <Clock className="w-3 h-3" />
            {showArchive ? "Ascunde" : "Arată"} istoric ({archives.length}{" "}
            {archives.length === 1 ? "versiune" : "versiuni"})
          </button>

          {showArchive && (
            <div className="mt-2 space-y-1">
              {archives.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between px-2 py-1.5 bg-[#0F172A] rounded border border-[#1E293B]"
                >
                  <div className="text-[10px] text-slate-400">
                    <span className="text-slate-300 font-medium">
                      v{a.quote_version}
                    </span>{" "}
                    • {formatDate(a.created_at)} • {formatBytes(a.file_size_bytes)}
                  </div>
                  <button
                    onClick={() => handleDownloadArchived(a.id)}
                    className="text-blue-400 hover:text-blue-300 p-1"
                    title="Descarcă această versiune"
                  >
                    <Download className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="text-[10px] text-slate-500 mt-2">Se încarcă...</div>
      )}
    </div>
  );
}