/**
 * BUILD 10 — Quote Output Snapshots Section.
 *
 * Displayed in Quotes detail view.
 * Shows saved output snapshot candidates with lifecycle actions.
 *
 * Rules:
 *   - No Quote mutation
 *   - No Order creation
 *   - No final contract generation
 *   - No email/send
 *   - Read-only display + controlled lifecycle actions
 */

import { useState, useCallback } from "react";
import {
  Archive,
  CheckCircle2,
  Download,
  Eye,
  FileText,
  Loader2,
  Plus,
  Send,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import {
  createOutputSnapshot,
  listOutputSnapshots,
  submitSnapshotForReview,
  approveSnapshot,
  archiveSnapshot,
  rejectSnapshot,
  getSnapshotExportUrl,
  type QuoteOutputSnapshotCandidate,
} from "@/api/quoteOutputSnapshots";

interface Props {
  quoteId: number;
  quoteCode: string;
}

export default function QuoteOutputSnapshotsSection({ quoteId, quoteCode }: Props) {
  const [snapshots, setSnapshots] = useState<QuoteOutputSnapshotCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [viewingSnapshot, setViewingSnapshot] = useState<QuoteOutputSnapshotCandidate | null>(null);

  const loadSnapshots = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listOutputSnapshots(quoteId);
      setSnapshots(data);
      setLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la incarcarea snapshoturilor");
    } finally {
      setLoading(false);
    }
  }, [quoteId]);

  const handleCreate = async () => {
    setActionLoading("create");
    setError(null);
    try {
      await createOutputSnapshot(quoteId, {
        notes: "Saved from composition preview",
        initial_status: "draft",
      });
      await loadSnapshots();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la crearea snapshotului");
    } finally {
      setActionLoading(null);
    }
  };

  const handleAction = async (
    snapshotId: number,
    action: "submit-review" | "approve" | "archive" | "reject"
  ) => {
    setActionLoading(`${action}-${snapshotId}`);
    setError(null);
    try {
      switch (action) {
        case "submit-review":
          await submitSnapshotForReview(quoteId, snapshotId);
          break;
        case "approve":
          await approveSnapshot(quoteId, snapshotId);
          break;
        case "archive":
          await archiveSnapshot(quoteId, snapshotId);
          break;
        case "reject":
          await rejectSnapshot(quoteId, snapshotId);
          break;
      }
      await loadSnapshots();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Eroare la actiunea ${action}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleExport = (snapshotId: number) => {
    const url = getSnapshotExportUrl(quoteId, snapshotId);
    window.open(url, "_blank");
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      draft: "bg-gray-100 text-gray-700 border-gray-300",
      needs_review: "bg-amber-50 text-amber-700 border-amber-300",
      approved_for_quote_output: "bg-green-50 text-green-700 border-green-300",
      archived: "bg-slate-100 text-slate-500 border-slate-300",
      superseded: "bg-blue-50 text-blue-500 border-blue-300",
      rejected: "bg-red-50 text-red-700 border-red-300",
    };
    const labels: Record<string, string> = {
      draft: "Draft",
      needs_review: "Needs Review",
      approved_for_quote_output: "Approved",
      archived: "Archived",
      superseded: "Superseded",
      rejected: "Rejected",
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${styles[status] || "bg-gray-100 text-gray-600 border-gray-200"}`}>
        {labels[status] || status}
      </span>
    );
  };

  const canSubmitReview = (s: QuoteOutputSnapshotCandidate) => s.status === "draft";
  const canApprove = (s: QuoteOutputSnapshotCandidate) =>
    (s.status === "draft" || s.status === "needs_review") && s.blockers.length === 0;
  const canArchive = (s: QuoteOutputSnapshotCandidate) =>
    !["archived", "superseded"].includes(s.status);
  const canReject = (s: QuoteOutputSnapshotCandidate) =>
    s.status === "draft" || s.status === "needs_review";

  return (
    <div className="mt-6 border border-slate-700 rounded-lg bg-slate-800/50 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-blue-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            Saved Output Snapshots
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {!loaded && (
            <button
              onClick={loadSnapshots}
              disabled={loading}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded bg-slate-700 text-slate-200 hover:bg-slate-600 disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Eye className="h-3 w-3" />}
              Load Snapshots
            </button>
          )}
          {loaded && (
            <button
              onClick={handleCreate}
              disabled={actionLoading === "create"}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50"
            >
              {actionLoading === "create" ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Plus className="h-3 w-3" />
              )}
              Save Current Preview
            </button>
          )}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="mb-3 px-3 py-2 bg-slate-900/50 border border-slate-600 rounded text-xs text-slate-400">
        <ShieldAlert className="inline h-3 w-3 mr-1 text-amber-400" />
        Saved quote output snapshot candidate. This is not an accepted order snapshot
        and does not change the quote or order.
      </div>

      {/* Error */}
      {error && (
        <div className="mb-3 px-3 py-2 bg-red-900/30 border border-red-700 rounded text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Snapshot list */}
      {loaded && snapshots.length === 0 && (
        <p className="text-xs text-slate-500 italic">
          No saved snapshots yet. Click &quot;Save Current Preview&quot; to create one.
        </p>
      )}

      {loaded && snapshots.length > 0 && (
        <div className="space-y-2">
          {snapshots.map((s) => (
            <div
              key={s.snapshot_id}
              className="border border-slate-700 rounded p-3 bg-slate-900/30"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-300">
                    {s.snapshot_code}
                  </span>
                  {getStatusBadge(s.status)}
                  <span className="text-xs text-slate-500">v{s.version}</span>
                </div>
                <span className="text-xs text-slate-500">
                  {s.created_at ? new Date(s.created_at).toLocaleString("ro-RO") : ""}
                </span>
              </div>

              {/* Warnings/blockers count */}
              <div className="flex items-center gap-3 mb-2 text-xs">
                {s.warnings.length > 0 && (
                  <span className="text-amber-400">
                    ⚠️ {s.warnings.length} warning{s.warnings.length > 1 ? "s" : ""}
                  </span>
                )}
                {s.blockers.length > 0 && (
                  <span className="text-red-400">
                    🚫 {s.blockers.length} blocker{s.blockers.length > 1 ? "s" : ""}
                  </span>
                )}
                {s.content_hash && (
                  <span className="text-slate-500 font-mono">
                    #{s.content_hash.slice(0, 8)}
                  </span>
                )}
                {s.source_template_code && (
                  <span className="text-slate-400">
                    {s.source_template_code}
                  </span>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1.5 flex-wrap">
                <button
                  onClick={() => setViewingSnapshot(viewingSnapshot?.snapshot_id === s.snapshot_id ? null : s)}
                  className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-slate-700 text-slate-300 hover:bg-slate-600"
                >
                  <Eye className="h-3 w-3" />
                  View
                </button>

                {canSubmitReview(s) && (
                  <button
                    onClick={() => handleAction(s.snapshot_id, "submit-review")}
                    disabled={actionLoading === `submit-review-${s.snapshot_id}`}
                    className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-amber-700 text-amber-100 hover:bg-amber-600 disabled:opacity-50"
                  >
                    <Send className="h-3 w-3" />
                    Submit for Review
                  </button>
                )}

                {canApprove(s) && (
                  <button
                    onClick={() => handleAction(s.snapshot_id, "approve")}
                    disabled={actionLoading === `approve-${s.snapshot_id}`}
                    className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-green-700 text-green-100 hover:bg-green-600 disabled:opacity-50"
                  >
                    <CheckCircle2 className="h-3 w-3" />
                    Approve for Quote Output
                  </button>
                )}

                {canArchive(s) && (
                  <button
                    onClick={() => handleAction(s.snapshot_id, "archive")}
                    disabled={actionLoading === `archive-${s.snapshot_id}`}
                    className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-slate-600 text-slate-300 hover:bg-slate-500 disabled:opacity-50"
                  >
                    <Archive className="h-3 w-3" />
                    Archive
                  </button>
                )}

                {canReject(s) && (
                  <button
                    onClick={() => handleAction(s.snapshot_id, "reject")}
                    disabled={actionLoading === `reject-${s.snapshot_id}`}
                    className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-red-800 text-red-200 hover:bg-red-700 disabled:opacity-50"
                  >
                    <XCircle className="h-3 w-3" />
                    Reject
                  </button>
                )}

                <button
                  onClick={() => handleExport(s.snapshot_id)}
                  className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-slate-700 text-slate-300 hover:bg-slate-600"
                >
                  <Download className="h-3 w-3" />
                  Export HTML
                </button>
              </div>

              {/* View detail */}
              {viewingSnapshot?.snapshot_id === s.snapshot_id && (
                <div className="mt-3 border-t border-slate-700 pt-3">
                  <div className="space-y-2">
                    {s.rendered_sections_json?.map((section, idx) => (
                      <div key={idx} className="bg-slate-800 rounded p-2 border border-slate-700">
                        <p className="text-xs font-medium text-blue-300 mb-1">
                          {section.title || `Section ${idx + 1}`}
                        </p>
                        <p className="text-xs text-slate-300 whitespace-pre-wrap">
                          {section.rendered_text || ""}
                        </p>
                      </div>
                    ))}
                    {s.commercial_summary_json && (
                      <div className="bg-slate-800 rounded p-2 border border-slate-700">
                        <p className="text-xs font-medium text-blue-300 mb-1">Commercial Summary</p>
                        <p className="text-xs text-slate-300">
                          Total: {s.commercial_summary_json.total?.toLocaleString("ro-RO")} {s.commercial_summary_json.currency || "RON"}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}