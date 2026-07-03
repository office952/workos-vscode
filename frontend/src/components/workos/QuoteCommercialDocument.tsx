/**
 * BUILD 5 — Quote Commercial Document Panel.
 *
 * Displays the client-facing commercial offer within the Quotes detail view.
 * Fetches data from the backend commercial-document endpoint.
 * Never recalculates pricing or readiness — displays backend truth only.
 */

import { useState, useEffect } from "react";
import {
  getQuoteCommercialDocument,
  downloadQuoteDocument,
  type CommercialDocument,
  type CommercialTerms,
} from "@/api/quoteDocuments";
import { StatusBadge } from "@/components/workos/design-system/StatusBadge";
import {
  FileText,
  Download,
  Eye,
  AlertTriangle,
  ExternalLink,
  Package,
  Layers,
  DollarSign,
  Clock,
  Shield,
  Truck,
  ChevronDown,
  ChevronUp,
  Loader2,
} from "lucide-react";

interface Props {
  quoteDbId: number | null;
  quoteCode: string;
  visible: boolean;
}

function formatCurrency(val: number): string {
  return val.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatValidityLabel(commercial: CommercialTerms, validUntil?: string | null): string {
  if (commercial.validity_display) {
    return commercial.validity_display;
  }
  const days = commercial.validity_days ?? 15;
  if (validUntil && validUntil.trim() && validUntil !== "—") {
    return `${days} zile (până la ${validUntil})`;
  }
  return `${days} zile de la emitere`;
}

function formatDocumentDate(iso?: string | null): string | null {
  if (!iso || !iso.trim()) return null;
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleDateString("ro-RO", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

export default function QuoteCommercialDocument({ quoteDbId, quoteCode, visible }: Props) {
  const [document, setDocument] = useState<CommercialDocument | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [sectionsExpanded, setSectionsExpanded] = useState<Record<string, boolean>>({
    product_description: true,
    technical_specs: false,
    line_items: true,
    commercial_terms: false,
    production_notes: false,
    externalization: true,
  });

  useEffect(() => {
    if (!visible || !quoteDbId) {
      setDocument(null);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    getQuoteCommercialDocument(quoteDbId)
      .then((doc) => {
        if (!cancelled) setDocument(doc);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Eroare la încărcarea documentului comercial");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [quoteDbId, visible]);

  const handleDownload = async () => {
    if (!quoteDbId) return;
    try {
      await downloadQuoteDocument(quoteDbId, "html");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Eroare la descărcare";
      alert(msg);
    }
  };

  const toggleSection = (id: string) => {
    setSectionsExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  if (!visible) return null;

  if (loading) {
    return (
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <div className="flex items-center gap-2 text-slate-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-[12px]">Se încarcă documentul comercial...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <div className="flex items-center gap-2 text-amber-400">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-[12px]">Document comercial indisponibil</span>
        </div>
        <p className="text-[10px] text-slate-500 mt-1">{error}</p>
      </div>
    );
  }

  if (!document) return null;

  const { product_text, totals, commercial, readiness, metadata, client } = document;
  const issueDate = formatDocumentDate(metadata.created_at ?? document.document.generated_at);
  const documentTitle =
    document.document.title || product_text?.client_title || document.product_summary?.product_name || "Ofertă comercială";

  return (
    <div className="space-y-3" data-testid="quote-commercial-document-panel">
      {/* Operator chrome — not part of client-facing document */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 flex-wrap min-w-0">
            <FileText className="w-4 h-4 text-blue-400 shrink-0" />
            <span className="text-[13px] font-bold text-slate-100">Ofertă pentru client</span>
            <span data-testid="commercial-document-operator-status">
              <StatusBadge domain="quote" status={document.status} className="text-[10px]" />
            </span>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={() => setPreviewOpen(!previewOpen)}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium rounded-md border border-slate-600/80 text-slate-300 hover:bg-slate-800/70 transition-colors"
              data-testid="commercial-document-preview-toggle"
            >
              <Eye className="w-3 h-3" />
              {previewOpen ? "Ascunde" : "Previzualizare"}
            </button>
            <button
              onClick={handleDownload}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium rounded-md border border-blue-600/70 text-blue-300 hover:bg-blue-900/30 transition-colors"
            >
              <Download className="w-3 h-3" />
              Descarcă HTML
            </button>
          </div>
        </div>

        {/* Quick summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="rounded-md border border-slate-700/50 bg-slate-900/30 px-2.5 py-2">
            <p className="text-[10px] text-slate-500 uppercase tracking-wide">Produs</p>
            <p className="text-[12px] text-slate-200 font-medium mt-0.5 leading-snug">
              {product_text?.client_title || document.product_summary?.product_name || "—"}
            </p>
          </div>
          <div className="rounded-md border border-slate-700/50 bg-slate-900/30 px-2.5 py-2">
            <p className="text-[10px] text-slate-500 uppercase tracking-wide">Total</p>
            <p className="text-[14px] text-slate-100 font-bold mt-0.5 tabular-nums">
              {formatCurrency(totals.grand_total)} {totals.currency}
            </p>
          </div>
          <div className="rounded-md border border-slate-700/50 bg-slate-900/30 px-2.5 py-2">
            <p className="text-[10px] text-slate-500 uppercase tracking-wide">Valabilitate</p>
            <p className="text-[12px] text-slate-300 mt-0.5 leading-snug">
              {formatValidityLabel(commercial, metadata.valid_until)}
            </p>
          </div>
          <div className="rounded-md border border-slate-700/50 bg-slate-900/30 px-2.5 py-2">
            <p className="text-[10px] text-slate-500 uppercase tracking-wide">TVA</p>
            <p className="text-[12px] text-slate-300 mt-0.5">{commercial.tva_percent}%</p>
          </div>
        </div>
      </div>

      {/* Client-facing document preview */}
      {previewOpen && (
        <div
          className="rounded-xl border border-slate-600/35 bg-[#0F1629] shadow-[0_4px_24px_rgba(0,0,0,0.22)] overflow-hidden"
          data-testid="commercial-document-preview"
        >
          <div className="px-5 py-4 border-b border-slate-600/30 bg-gradient-to-b from-slate-800/35 to-transparent">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500">Document comercial</p>
                <h2 className="text-[17px] font-bold text-slate-50 mt-1 leading-tight">{documentTitle}</h2>
                <p
                  className="text-[12px] font-mono text-blue-300/90 mt-1"
                  data-testid="commercial-document-quote-code"
                >
                  {document.quote_code || quoteCode}
                </p>
              </div>
              <div className="text-[11px] text-slate-400 space-y-0.5 sm:text-right shrink-0">
                {issueDate ? (
                  <p data-testid="commercial-document-issue-date">Emitere: {issueDate}</p>
                ) : null}
                <p data-testid="commercial-document-validity">
                  Valabilitate: {formatValidityLabel(commercial, metadata.valid_until)}
                </p>
                {document.version > 0 ? <p>Versiune {document.version}</p> : null}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-700/40 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div data-testid="commercial-document-client-block">
                <p className="text-[10px] uppercase tracking-wide text-slate-500">Client</p>
                <p className="text-[13px] font-semibold text-slate-100 mt-0.5">{client.name || "—"}</p>
                {client.company ? (
                  <p className="text-[11px] text-slate-400 mt-0.5">{client.company}</p>
                ) : null}
                {client.contact_person ? (
                  <p className="text-[11px] text-slate-500 mt-0.5">{client.contact_person}</p>
                ) : null}
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wide text-slate-500">Produs ofertat</p>
                <p className="text-[13px] text-slate-200 mt-0.5 leading-snug">
                  {product_text?.client_title || document.product_summary?.product_name || "—"}
                </p>
              </div>
            </div>
          </div>

          <div className="p-3 space-y-2">
          {/* Product Description */}
          <CollapsibleSection
            id="product_description"
            title="Descriere produs"
            icon={<Package className="w-3.5 h-3.5" />}
            expanded={sectionsExpanded.product_description}
            onToggle={() => toggleSection("product_description")}
          >
            <p className="text-[12px] text-slate-200 font-medium mb-1">
              {product_text?.client_title || "—"}
            </p>
            <p className="text-[11px] text-slate-300">
              {product_text?.short_description || "—"}
            </p>
            {product_text?.technical_description && (
              <p className="text-[11px] text-slate-400 mt-2 italic">
                {product_text.technical_description}
              </p>
            )}
          </CollapsibleSection>

          {/* Technical Specs */}
          {(product_text?.materials_summary || product_text?.operations_summary) && (
            <CollapsibleSection
              id="technical_specs"
              title="Specificații tehnice"
              icon={<Layers className="w-3.5 h-3.5" />}
              expanded={sectionsExpanded.technical_specs}
              onToggle={() => toggleSection("technical_specs")}
            >
              {product_text?.materials_summary && (
                <div className="mb-2">
                  <p className="text-[10px] text-slate-500 uppercase mb-0.5">Materiale</p>
                  <p className="text-[11px] text-slate-300">{product_text.materials_summary}</p>
                </div>
              )}
              {product_text?.operations_summary && (
                <div className="mb-2">
                  <p className="text-[10px] text-slate-500 uppercase mb-0.5">Operații</p>
                  <p className="text-[11px] text-slate-300">{product_text.operations_summary}</p>
                </div>
              )}
              {product_text?.included_finishes && (
                <div className="mb-2">
                  <p className="text-[10px] text-slate-500 uppercase mb-0.5">Finisaje incluse</p>
                  <p className="text-[11px] text-slate-300">{product_text.included_finishes}</p>
                </div>
              )}
              {product_text?.optional_finishes && (
                <div>
                  <p className="text-[10px] text-slate-500 uppercase mb-0.5">Finisaje opționale</p>
                  <p className="text-[11px] text-slate-300">{product_text.optional_finishes}</p>
                </div>
              )}
            </CollapsibleSection>
          )}

          {/* Line Items */}
          <CollapsibleSection
            id="line_items"
            title="Detaliere preț"
            icon={<DollarSign className="w-3.5 h-3.5" />}
            expanded={sectionsExpanded.line_items}
            onToggle={() => toggleSection("line_items")}
          >
            <div className="space-y-0.5">
              <div className="grid grid-cols-[1fr_auto] gap-2 text-[9px] uppercase tracking-wide text-slate-500 px-0.5 pb-1 border-b border-slate-700/40">
                <span>Descriere</span>
                <span className="text-right">Valoare</span>
              </div>
              {document.line_items.map((item, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-[1fr_auto] gap-2 items-start py-2 border-b border-slate-700/40 last:border-0"
                  data-testid={idx === 0 ? "commercial-document-line-item" : undefined}
                >
                  <div>
                    <p className="text-[11px] text-slate-200 leading-snug">{item.description}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-[11px] text-slate-200 font-medium tabular-nums">
                      {formatCurrency(item.total)} {totals.currency}
                    </p>
                    <p className="text-[9px] text-slate-500 tabular-nums">
                      {item.quantity} × {formatCurrency(item.unit_price)}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Totals */}
            <div
              className="mt-4 rounded-lg border border-slate-600/40 bg-slate-900/45 px-3 py-2.5 space-y-1.5"
              data-testid="commercial-document-financial-summary"
            >
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400">Subtotal</span>
                <span className="text-slate-200 tabular-nums">
                  {formatCurrency(totals.subtotal)} {totals.currency}
                </span>
              </div>
              {totals.discount > 0 && (
                <div className="flex justify-between text-[11px] text-amber-400">
                  <span>Discount ({totals.discount_pct}%)</span>
                  <span className="tabular-nums">
                    -{formatCurrency(totals.discount)} {totals.currency}
                  </span>
                </div>
              )}
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400">TVA ({commercial.tva_percent}%)</span>
                <span className="text-slate-200 tabular-nums" data-testid="commercial-document-tva">
                  {formatCurrency(totals.tva)} {totals.currency}
                </span>
              </div>
              <div className="flex justify-between items-baseline pt-2 mt-1 border-t border-slate-500/50">
                <span className="text-[12px] font-bold tracking-wide text-slate-100">TOTAL</span>
                <span
                  className="text-[15px] font-bold text-slate-50 tabular-nums"
                  data-testid="commercial-document-grand-total"
                >
                  {formatCurrency(totals.grand_total)} {totals.currency}
                </span>
              </div>
            </div>
          </CollapsibleSection>

          {/* Commercial Terms */}
          <CollapsibleSection
            id="commercial_terms"
            title="Condiții comerciale"
            icon={<Shield className="w-3.5 h-3.5" />}
            expanded={sectionsExpanded.commercial_terms}
            onToggle={() => toggleSection("commercial_terms")}
          >
            <div className="space-y-1.5 text-[11px]">
              <div className="flex items-start gap-2">
                <Clock className="w-3 h-3 text-slate-500 mt-0.5 shrink-0" />
                <span className="text-slate-300">
                  Valabilitate: {formatValidityLabel(commercial, metadata.valid_until)}
                </span>
              </div>
              {commercial.payment_terms && (
                <div className="flex items-start gap-2">
                  <DollarSign className="w-3 h-3 text-slate-500 mt-0.5 shrink-0" />
                  <span className="text-slate-300">Plată: {commercial.payment_terms}</span>
                </div>
              )}
              {commercial.delivery_terms && (
                <div className="flex items-start gap-2">
                  <Truck className="w-3 h-3 text-slate-500 mt-0.5 shrink-0" />
                  <span className="text-slate-300">Livrare: {commercial.delivery_terms}</span>
                </div>
              )}
              {commercial.warranty_terms && (
                <div className="flex items-start gap-2">
                  <Shield className="w-3 h-3 text-slate-500 mt-0.5 shrink-0" />
                  <span className="text-slate-300">Garanție: {commercial.warranty_terms}</span>
                </div>
              )}
            </div>
          </CollapsibleSection>

          {/* Production Notes */}
          {(product_text?.production_assumptions || product_text?.limitations) && (
            <CollapsibleSection
              id="production_notes"
              title="Observații producție"
              icon={<AlertTriangle className="w-3.5 h-3.5" />}
              expanded={sectionsExpanded.production_notes}
              onToggle={() => toggleSection("production_notes")}
            >
              {product_text?.production_assumptions && (
                <p className="text-[11px] text-slate-300 mb-2">
                  {product_text.production_assumptions}
                </p>
              )}
              {product_text?.limitations && (
                <p className="text-[11px] text-amber-400/80">
                  <strong>Limitări:</strong> {product_text.limitations}
                </p>
              )}
            </CollapsibleSection>
          )}

          {/* Externalization */}
          {product_text?.externalization_note && (
            <CollapsibleSection
              id="externalization"
              title="Externalizare"
              icon={<ExternalLink className="w-3.5 h-3.5" />}
              expanded={sectionsExpanded.externalization}
              onToggle={() => toggleSection("externalization")}
            >
              <div className="bg-amber-900/20 border border-amber-700/40 rounded p-2.5">
                <p className="text-[11px] text-amber-300">
                  {product_text.externalization_note}
                </p>
              </div>
            </CollapsibleSection>
          )}

          {/* Readiness Notes (internal) */}
          {(readiness.warnings.length > 0 || readiness.blockers.length > 0) && (
            <div
              className="rounded-lg border border-red-800/35 bg-red-950/15 px-3 py-2.5"
              data-testid="commercial-document-readiness-notes"
            >
              <p className="text-[10px] text-red-400 font-semibold uppercase tracking-wide mb-1.5">
                Note pregătire producție
              </p>
              {readiness.blockers.length > 0 && (
                <div className="mb-1.5 space-y-0.5">
                  {readiness.blockers.map((b, i) => (
                    <p key={i} className="text-[10px] text-red-300" data-testid="commercial-document-blocker">
                      • Blocker: {b}
                    </p>
                  ))}
                </div>
              )}
              {readiness.warnings.length > 0 && (
                <div className="space-y-0.5">
                  {readiness.warnings.map((w, i) => (
                    <p key={i} className="text-[10px] text-amber-300" data-testid="commercial-document-warning">
                      • Warning: {w}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Collapsible Section helper
// ---------------------------------------------------------------------------
function CollapsibleSection({
  id,
  title,
  icon,
  expanded,
  onToggle,
  children,
}: {
  id: string;
  title: string;
  icon: React.ReactNode;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-slate-900/45 border border-slate-600/30 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2.5 hover:bg-slate-800/55 transition-colors"
        aria-expanded={expanded}
        data-section-id={id}
      >
        <div className="flex items-center gap-2 text-slate-300">
          {icon}
          <span className="text-[11px] font-semibold uppercase tracking-wide">{title}</span>
        </div>
        {expanded ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-500" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
        )}
      </button>
      {expanded && <div className="px-3 pb-3">{children}</div>}
    </div>
  );
}