/**
 * BUILD 8 — Output Blocks Read-Only Preview UI.
 *
 * Route: /product-system/output-blocks-preview
 *
 * Purpose:
 *   Read-only preview of rendered Output Blocks.
 *   No save, no create quote, no create order, no send, no export, no snapshot.
 *
 * UI allows:
 *   - Select template / dossier
 *   - Choose document_type
 *   - Choose audience
 *   - Choose block types
 *   - Enter minimal preview context (client_name, quantity, dimensions)
 *   - Button: Render preview
 *   - Display rendered blocks, warnings, blockers, variables_used, trace
 *
 * UI does NOT allow:
 *   - Editing blocks from preview
 *   - Saving rendered text
 *   - Auto-fix missing variables
 *   - Price calculation
 *   - Quote creation
 *   - Order creation
 *   - Contract generation
 *   - Local readiness calculation
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, Eye, FileText, Info, Loader2, ShieldAlert } from "lucide-react";
import {
  type RenderPreviewResponse,
  type RenderedBlock,
} from "@/api/outputBlocksPreview";
import { renderOutputBlocksPreviewWave2 } from "@/api/outputBlocksPreviewWave2Orchestrator";

const DOCUMENT_TYPES = [
  "offer",
  "contract",
  "technical_memo",
  "production_sheet",
  "installation_sheet",
  "warranty_document",
  "maintenance_document",
  "internal_note",
];

const AUDIENCES = [
  "client",
  "internal",
  "production",
  "technical",
  "legal_commercial",
  "installation",
  "sales",
  "estimator",
];

const BLOCK_TYPES = [
  "offer_short_description",
  "offer_technical_description",
  "contract_scope_included",
  "contract_scope_excluded",
  "technical_memo_description",
  "technical_memo_materials",
  "technical_memo_execution_method",
  "production_instruction",
  "installation_note",
  "warranty_note",
  "maintenance_note",
  "exclusion_assumption",
  "qc_note",
  "risk_note",
];

export default function OutputBlocksPreview() {
  const [templateId, setTemplateId] = useState<string>("");
  const [documentType, setDocumentType] = useState("offer");
  const [audience, setAudience] = useState("client");
  const [selectedBlockTypes, setSelectedBlockTypes] = useState<string[]>([]);
  const [clientName, setClientName] = useState("Client preview");
  const [quantity, setQuantity] = useState("1");
  const [widthMm, setWidthMm] = useState("");
  const [heightMm, setHeightMm] = useState("");
  const [depthMm, setDepthMm] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RenderPreviewResponse | null>(null);

  const handleRenderPreview = async () => {
    if (!templateId) {
      setError("Template ID este obligatoriu.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const dimensions: Record<string, number> = {};
      if (widthMm) dimensions.width_mm = parseInt(widthMm, 10);
      if (heightMm) dimensions.height_mm = parseInt(heightMm, 10);
      if (depthMm) dimensions.depth_mm = parseInt(depthMm, 10);

      const response = await renderOutputBlocksPreviewWave2({
        template_id: parseInt(templateId, 10),
        document_type: documentType,
        audience,
        block_types: selectedBlockTypes.length > 0 ? selectedBlockTypes : undefined,
        quote_context: {
          client_name: clientName,
          quantity: parseInt(quantity, 10) || 1,
          dimensions: Object.keys(dimensions).length > 0 ? dimensions : undefined,
        },
        render_mode: "preview",
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare necunoscuta");
    } finally {
      setLoading(false);
    }
  };

  const toggleBlockType = (bt: string) => {
    setSelectedBlockTypes((prev) =>
      prev.includes(bt) ? prev.filter((x) => x !== bt) : [...prev, bt]
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Eye className="w-6 h-6 text-purple-400" />
        <div>
          <h1 className="text-xl font-bold text-slate-100">Output Blocks Preview</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Read-only render preview — ProductSystem / Blueprint Dossier
          </p>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-2 px-3 py-2 rounded-lg border border-amber-800/50 bg-amber-900/20">
        <Info className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <p className="text-[11px] text-amber-300">
          Preview only. Output is not saved, not sent, and not part of any accepted order snapshot.
        </p>
      </div>

      {/* BUILD 10 — Snapshot indicator */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-blue-800/50 bg-blue-900/20">
        <FileText className="w-4 h-4 text-blue-400 shrink-0" />
        <p className="text-[11px] text-blue-300">
          To save a snapshot of this output, navigate to the Quote detail view and use &quot;Save Current Preview&quot; in the Saved Output Snapshots section.
        </p>
      </div>

      {/* Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Configuration */}
        <div className="space-y-4 rounded-lg border border-wo-border-subtle bg-wo-surface-raised p-4">
          <h2 className="text-sm font-semibold text-slate-200">Configurare Preview</h2>

          {/* Template ID */}
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Template ID *</label>
            <input
              type="number"
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value)}
              placeholder="ex: 1"
              className="w-full px-3 py-1.5 rounded border border-wo-border-strong bg-wo-surface-inset text-slate-200 text-[12px] outline-none focus:border-purple-500"
            />
          </div>

          {/* Document Type */}
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Document Type</label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="w-full px-3 py-1.5 rounded border border-wo-border-strong bg-wo-surface-inset text-slate-200 text-[12px] outline-none focus:border-purple-500"
            >
              {DOCUMENT_TYPES.map((dt) => (
                <option key={dt} value={dt}>{dt}</option>
              ))}
            </select>
          </div>

          {/* Audience */}
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Audience</label>
            <select
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              className="w-full px-3 py-1.5 rounded border border-wo-border-strong bg-wo-surface-inset text-slate-200 text-[12px] outline-none focus:border-purple-500"
            >
              {AUDIENCES.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>

          {/* Block Types */}
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">
              Block Types (optional — all if empty)
            </label>
            <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
              {BLOCK_TYPES.map((bt) => (
                <button
                  key={bt}
                  onClick={() => toggleBlockType(bt)}
                  className={`px-2 py-0.5 rounded text-[10px] border transition-colors ${
                    selectedBlockTypes.includes(bt)
                      ? "border-purple-500 bg-purple-900/30 text-purple-300"
                      : "border-wo-border-strong bg-wo-surface-inset text-slate-400 hover:border-slate-600"
                  }`}
                >
                  {bt.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>

          {/* Quote Context */}
          <div className="space-y-2 pt-2 border-t border-wo-border-subtle">
            <h3 className="text-[11px] font-semibold text-slate-300">Context Preview (optional)</h3>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[10px] text-slate-500 mb-0.5">Client Name</label>
                <input
                  type="text"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  className="w-full px-2 py-1 rounded border border-wo-border-strong bg-wo-surface-inset text-slate-200 text-[11px] outline-none"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-500 mb-0.5">Quantity</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  className="w-full px-2 py-1 rounded border border-wo-border-strong bg-wo-surface-inset text-slate-200 text-[11px] outline-none"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-500 mb-0.5">Width (mm)</label>
                <input
                  type="number"
                  value={widthMm}
                  onChange={(e) => setWidthMm(e.target.value)}
                  placeholder="1000"
                  className="w-full px-2 py-1 rounded border border-wo-border-strong bg-wo-surface-inset text-slate-200 text-[11px] outline-none"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-500 mb-0.5">Height (mm)</label>
                <input
                  type="number"
                  value={heightMm}
                  onChange={(e) => setHeightMm(e.target.value)}
                  placeholder="500"
                  className="w-full px-2 py-1 rounded border border-wo-border-strong bg-wo-surface-inset text-slate-200 text-[11px] outline-none"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-500 mb-0.5">Depth (mm)</label>
                <input
                  type="number"
                  value={depthMm}
                  onChange={(e) => setDepthMm(e.target.value)}
                  placeholder="80"
                  className="w-full px-2 py-1 rounded border border-wo-border-strong bg-wo-surface-inset text-slate-200 text-[11px] outline-none"
                />
              </div>
            </div>
          </div>

          {/* Render Button */}
          <button
            onClick={handleRenderPreview}
            disabled={loading || !templateId}
            className="w-full mt-2 px-4 py-2 rounded bg-purple-600 hover:bg-purple-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-[12px] font-medium transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Se randeaza...
              </>
            ) : (
              <>
                <Eye className="w-3.5 h-3.5" />
                Render Preview
              </>
            )}
          </button>
        </div>

        {/* Right: Results */}
        <div className="space-y-3 rounded-lg border border-wo-border-subtle bg-wo-surface-raised p-4">
          <h2 className="text-sm font-semibold text-slate-200">Rezultat Preview</h2>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 px-3 py-2 rounded border border-red-800/50 bg-red-900/20">
              <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
              <p className="text-[11px] text-red-300">{error}</p>
            </div>
          )}

          {/* Empty state */}
          {!result && !error && !loading && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="w-8 h-8 text-slate-600 mb-2" />
              <p className="text-[12px] text-slate-500">
                Selecteaza un template si apasa &quot;Render Preview&quot;
              </p>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 text-purple-400 animate-spin" />
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-3">
              {/* Meta */}
              <div className="flex flex-wrap gap-2 text-[10px]">
                <span className="px-2 py-0.5 rounded bg-green-900/30 border border-green-800/50 text-green-300">
                  persisted: false
                </span>
                <span className="px-2 py-0.5 rounded bg-blue-900/30 border border-blue-800/50 text-blue-300">
                  mode: {result.render_mode}
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                  template: {result.template_id ?? "—"}
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                  dossier: {result.dossier_id ?? "—"}
                </span>
              </div>

              {/* Blockers */}
              {result.blockers.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-red-400 uppercase">Blockers</p>
                  {result.blockers.map((b, i) => (
                    <div key={i} className="flex items-start gap-1.5 px-2 py-1 rounded bg-red-900/20 border border-red-800/40">
                      <ShieldAlert className="w-3 h-3 text-red-400 mt-0.5 shrink-0" />
                      <span className="text-[10px] text-red-300">{b}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Warnings */}
              {result.warnings.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-amber-400 uppercase">Warnings</p>
                  {result.warnings.map((w, i) => (
                    <div key={i} className="flex items-start gap-1.5 px-2 py-1 rounded bg-amber-900/20 border border-amber-800/40">
                      <AlertTriangle className="w-3 h-3 text-amber-400 mt-0.5 shrink-0" />
                      <span className="text-[10px] text-amber-300">{w}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Rendered Blocks */}
              {result.blocks.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] font-bold text-slate-300 uppercase">
                    Rendered Blocks ({result.blocks.length})
                  </p>
                  {result.blocks.map((block, i) => (
                    <RenderedBlockCard key={i} block={block} />
                  ))}
                </div>
              )}

              {/* Empty blocks */}
              {result.blocks.length === 0 && result.blockers.length === 0 && (
                <p className="text-[11px] text-slate-500 italic">
                  Niciun block randat pentru filtrele selectate.
                </p>
              )}

              {/* Trace */}
              <div className="pt-2 border-t border-wo-border-subtle">
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Trace</p>
                <pre className="text-[9px] text-slate-500 bg-wo-surface-inset rounded p-2 overflow-x-auto">
                  {JSON.stringify(result.trace, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function RenderedBlockCard({ block }: { block: RenderedBlock }) {
  const [showVars, setShowVars] = useState(false);

  return (
    <div className="rounded border border-wo-border-strong bg-wo-surface-inset p-3 space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium text-slate-200">{block.title || block.block_id}</span>
          <span className="px-1.5 py-0.5 rounded text-[9px] bg-slate-800 text-slate-400 border border-slate-700">
            {block.block_type.replace(/_/g, " ")}
          </span>
        </div>
        <span
          className={`px-1.5 py-0.5 rounded text-[9px] border ${
            block.approval_status === "approved" || block.approval_status === "approved_for_client"
              ? "bg-green-900/30 border-green-800/50 text-green-300"
              : block.approval_status === "deprecated"
              ? "bg-red-900/30 border-red-800/50 text-red-300"
              : "bg-slate-800 border-slate-700 text-slate-400"
          }`}
        >
          {block.approval_status}
        </span>
      </div>

      {/* Rendered text */}
      <div className="rounded bg-wo-surface-inset p-2">
        <p className="text-[11px] text-slate-300 whitespace-pre-wrap leading-relaxed">
          {block.rendered_text || <span className="italic text-slate-600">— empty —</span>}
        </p>
      </div>

      {/* Block warnings */}
      {block.warnings.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {block.warnings.map((w, i) => (
            <span key={i} className="px-1.5 py-0.5 rounded text-[9px] bg-amber-900/20 border border-amber-800/40 text-amber-300">
              {w}
            </span>
          ))}
        </div>
      )}

      {/* Block blockers */}
      {block.blockers.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {block.blockers.map((b, i) => (
            <span key={i} className="px-1.5 py-0.5 rounded text-[9px] bg-red-900/20 border border-red-800/40 text-red-300">
              {b}
            </span>
          ))}
        </div>
      )}

      {/* Variables toggle */}
      {block.variables_used.length > 0 && (
        <div>
          <button
            onClick={() => setShowVars(!showVars)}
            className="text-[10px] text-purple-400 hover:text-purple-300 transition-colors"
          >
            {showVars ? "▼" : "▶"} Variables ({block.variables_used.length})
          </button>
          {showVars && (
            <div className="mt-1 space-y-0.5">
              {block.variables_used.map((v, i) => (
                <div key={i} className="flex items-center gap-2 text-[9px] px-2 py-0.5 rounded bg-wo-surface-inset">
                  <span className="text-slate-400 font-mono">{v.name}</span>
                  <span className="text-slate-600">←</span>
                  <span className="text-slate-500 font-mono">{v.source_field}</span>
                  <span className="text-slate-600">=</span>
                  <span className={v.resolved ? "text-green-400" : "text-red-400"}>
                    {v.resolved ? String(v.value) : "⚠ unresolved"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}