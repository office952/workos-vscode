/**
 * Read-only "Documente importante" panel for Governance → Surse de adevăr.
 * Consumes B2 allowlisted index only — not a Documentation Center.
 */

import { useState } from "react";
import { BookOpen, Loader2, AlertTriangle, X, Eye } from "lucide-react";
import { SectionHeader } from "@/components/workos/SharedComponents";
import {
  fetchDocumentationDetail,
  isAttentionStatus,
  type DocumentationIndexFetchResult,
  type DocumentationIndexItem,
} from "@/api/documentationIndex";

function StatusChips({ doc }: { doc: DocumentationIndexItem }) {
  const flags = isAttentionStatus(doc.status, doc.authority, doc.drift_status);
  return (
    <div className="flex flex-wrap gap-1.5">
      <span className="px-1.5 py-0.5 text-[9px] font-semibold rounded border border-slate-600 text-slate-300">
        {doc.authority}
      </span>
      <span className="px-1.5 py-0.5 text-[9px] font-semibold rounded border border-amber-800/40 text-amber-300/90">
        {doc.status}
      </span>
      {flags.stale && (
        <span
          className="px-1.5 py-0.5 text-[9px] font-semibold rounded border border-amber-700 text-amber-200 bg-amber-900/30"
          data-testid="doc-flag-stale"
        >
          STALE
        </span>
      )}
      {flags.superseded && (
        <span
          className="px-1.5 py-0.5 text-[9px] font-semibold rounded border border-red-800 text-red-300 bg-red-900/20"
          data-testid="doc-flag-superseded"
        >
          SUPERSEDED
        </span>
      )}
      {flags.ownerReview && (
        <span
          className="px-1.5 py-0.5 text-[9px] font-semibold rounded border border-amber-700 text-amber-200 bg-amber-900/30"
          data-testid="doc-flag-owner-review"
        >
          OWNER REVIEW REQUIRED
        </span>
      )}
      {doc.drift_status && doc.drift_status !== "ALIGNED" && (
        <span className="px-1.5 py-0.5 text-[9px] font-semibold rounded border border-slate-600 text-slate-400">
          drift: {doc.drift_status}
        </span>
      )}
    </div>
  );
}

function documentRole(doc: DocumentationIndexItem): string {
  return (
    doc.display?.display_label_ro ||
    doc.display?.technical_alias ||
    doc.category ||
    "—"
  );
}

function documentDescription(doc: DocumentationIndexItem): string {
  if (doc.display?.description_ro?.trim()) {
    return doc.display.description_ro.trim();
  }
  return `Document allowlisted în indexul B2 (${doc.category}). Prezența în index nu implică status canonic.`;
}

export function ImportantDocumentsSection({
  docsResult,
}: {
  docsResult: DocumentationIndexFetchResult | null;
}) {
  const [openId, setOpenId] = useState<string | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [contentError, setContentError] = useState<string | null>(null);
  const [contentBody, setContentBody] = useState<string | null>(null);
  const [contentReason, setContentReason] = useState<string | null>(null);

  const openDocument = async (documentId: string) => {
    setOpenId(documentId);
    setContentLoading(true);
    setContentError(null);
    setContentBody(null);
    setContentReason(null);
    const result = await fetchDocumentationDetail(documentId, true);
    setContentLoading(false);
    if (result.state === "forbidden") {
      setContentError("Acces interzis pentru conținut (system.documentation_read).");
      return;
    }
    if (result.state === "not_found") {
      setContentError("Document indisponibil în index (sau neallowlisted).");
      return;
    }
    if (result.state === "unavailable") {
      setContentError(`Conținut indisponibil: ${result.message}`);
      return;
    }
    setContentReason(result.data.reason_for_inclusion);
    if (!result.data.file_exists) {
      setContentError("Fișierul nu există pe disc (index allowlisted, dar lipsește fișierul).");
      return;
    }
    if (!result.data.content_markdown) {
      setContentError("Conținutul nu a putut fi încărcat (sau e gol).");
      return;
    }
    setContentBody(result.data.content_markdown);
  };

  const closeDocument = () => {
    setOpenId(null);
    setContentBody(null);
    setContentError(null);
    setContentReason(null);
  };

  return (
    <section
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4"
      data-testid="governance-important-documents"
    >
      <SectionHeader title="Documente importante" icon={<BookOpen className="w-4 h-4 text-blue-400" />} />
      <p className="text-[11px] text-slate-500 mb-3">
        Corpus allowlisted din indexul B2 (read-only). Nu este Centrul de documentație și nu listează tot{" "}
        <code className="text-slate-400">docs/</code>.
      </p>

      {docsResult === null && (
        <div
          className="flex items-center gap-2 text-[12px] text-slate-400 py-4"
          data-testid="important-docs-loading"
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          Se încarcă documentele indexate...
        </div>
      )}

      {docsResult?.state === "forbidden" && (
        <div
          className="flex items-start gap-2 px-3 py-2 rounded border border-amber-800/40 bg-amber-900/15 text-[12px] text-amber-200"
          data-testid="important-docs-forbidden"
        >
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          Acces interzis. Este necesară permisiunea{" "}
          <code className="text-amber-100">system.documentation_read</code> (admin).
        </div>
      )}

      {docsResult?.state === "unavailable" && (
        <div
          className="px-3 py-2 rounded border border-red-800/40 bg-red-900/20 text-[12px] text-red-300"
          data-testid="important-docs-unavailable"
        >
          API index documentație indisponibil: {docsResult.message}
        </div>
      )}

      {docsResult?.state === "empty" && (
        <div
          className="px-3 py-2 rounded border border-slate-600 bg-slate-800/40 text-[12px] text-slate-400"
          data-testid="important-docs-empty"
        >
          Listă goală — niciun document allowlisted în index.
        </div>
      )}

      {docsResult?.state === "ok" && (
        <div className="space-y-2" data-testid="important-docs-list">
          <p className="text-[10px] text-slate-500 mb-1">
            {docsResult.data.count} documente din index · {docsResult.data.index_version}
          </p>
          {docsResult.data.items.map((doc) => (
            <div
              key={doc.document_id}
              className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3"
              data-testid={`important-doc-${doc.document_id}`}
            >
              <div className="flex flex-wrap items-start gap-2 mb-1.5">
                <p className="text-[13px] font-semibold text-slate-100">{doc.title}</p>
                <StatusChips doc={doc} />
              </div>
              <p className="text-[11px] text-slate-400 mb-2">{documentDescription(doc)}</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1 text-[10px] text-slate-500">
                <p>
                  <span className="text-slate-600">document_id:</span>{" "}
                  <code className="text-slate-400">{doc.document_id}</code>
                </p>
                <p>
                  <span className="text-slate-600">rol:</span> {documentRole(doc)}
                </p>
                <p>
                  <span className="text-slate-600">categorie:</span> {doc.category}
                </p>
                <p>
                  <span className="text-slate-600">validat:</span>{" "}
                  {doc.last_validated_at
                    ? new Date(doc.last_validated_at).toLocaleString("ro-RO")
                    : "Neverificat / lipsă"}
                </p>
                <p className="md:col-span-2">
                  <span className="text-slate-600">path:</span>{" "}
                  <code className="text-slate-400 break-all">{doc.path}</code>
                </p>
                <p>
                  <span className="text-slate-600">sisteme:</span>{" "}
                  {doc.related_systems?.length ? doc.related_systems.join(", ") : "—"}
                </p>
                <p>
                  <span className="text-slate-600">pagini:</span>{" "}
                  {doc.related_pages?.length ? doc.related_pages.join(", ") : "—"}
                </p>
              </div>
              <button
                type="button"
                className="mt-2 inline-flex items-center gap-1.5 px-2 py-1 text-[11px] rounded border border-blue-700/40 text-blue-300 hover:bg-blue-900/20"
                data-testid={`important-doc-open-${doc.document_id}`}
                onClick={() => openDocument(doc.document_id)}
              >
                <Eye className="w-3.5 h-3.5" />
                Deschide (read-only)
              </button>
            </div>
          ))}
        </div>
      )}

      {openId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          data-testid="important-docs-reader"
          role="dialog"
          aria-modal="true"
          aria-label="Document read-only"
        >
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg max-w-3xl w-full max-h-[85vh] flex flex-col shadow-xl">
            <div className="flex items-center justify-between gap-2 px-4 py-3 border-b border-wo-border-subtle">
              <div>
                <p className="text-[13px] font-semibold text-slate-100">Citire read-only</p>
                <p className="text-[10px] text-slate-500 font-mono">{openId}</p>
              </div>
              <button
                type="button"
                onClick={closeDocument}
                className="p-1 rounded hover:bg-slate-700 text-slate-400"
                aria-label="Închide"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="px-4 py-3 overflow-y-auto flex-1 text-[12px]">
              {contentLoading && (
                <div className="flex items-center gap-2 text-slate-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Se încarcă conținutul...
                </div>
              )}
              {contentError && <p className="text-red-300">{contentError}</p>}
              {contentReason && (
                <p className="text-slate-400 mb-2">
                  <span className="text-slate-500">Rol / includere:</span> {contentReason}
                </p>
              )}
              {contentBody && (
                <pre className="whitespace-pre-wrap break-words text-slate-300 font-mono text-[11px] leading-relaxed">
                  {contentBody}
                </pre>
              )}
            </div>
            <div className="px-4 py-2 border-t border-wo-border-subtle text-[10px] text-slate-600">
              Fără editare · fără upload · lookup doar după document_id
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
