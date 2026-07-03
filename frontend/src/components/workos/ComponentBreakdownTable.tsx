/**
 * Sprint #18 — ComponentBreakdownTable
 *
 * Read-only visual reflection of `quote.componentBreakdown` (Sprint #17
 * CostEngine v2 output). Renders:
 *
 *   • A main table: Component (type + name) | Material | Operation | Total
 *   • Expandable rows per component:
 *       - materials_detail[]: code | qty | unit | unit_cost | line_total
 *       - operations_detail[]: code | workcenter | est.min | hours | rate/h | line_total
 *       - errors[] (if any)   — red pills
 *       - warnings[] (if any) — amber pills ("Componentă goală" when COMPONENT_EMPTY)
 *
 * HARD rules:
 *   - ZERO math. Numbers are displayed exactly as provided by the backend.
 *   - ZERO backend calls. Receives data via props only.
 *   - Styling: Tailwind inline (same slate/dark palette as Quotes.tsx,
 *     keeps visual parity with the surrounding panels).
 *   - Keyboard + screen-reader friendly: expand is a <button> with
 *     aria-expanded/aria-controls.
 */
import { useState } from "react";
import { ChevronDown, ChevronRight, AlertTriangle, AlertCircle } from "lucide-react";
import type { ComponentBreakdownItem } from "@/lib/mockData";

function formatNumber(val: number | undefined | null, digits = 2): string {
  if (val === undefined || val === null || Number.isNaN(val)) return "—";
  return Number(val).toLocaleString("ro-RO", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

interface ComponentBreakdownTableProps {
  components: ComponentBreakdownItem[];
}

/**
 * Single component row — header (always visible) + collapsible details.
 */
function ComponentRow({ comp, index }: { comp: ComponentBreakdownItem; index: number }) {
  const [open, setOpen] = useState(false);

  const title = comp.name || comp.component_id || `Componentă ${index + 1}`;
  const subtitle = comp.type || "";
  const errors = comp.errors ?? [];
  const warnings = comp.warnings ?? [];
  const hasIssues = errors.length > 0 || warnings.length > 0;
  const detailsId = `cbd-details-${comp.component_id ?? index}`;

  return (
    <div className="border border-[#2A3548] rounded-lg overflow-hidden bg-[#1A2236]">
      {/* Header row */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={detailsId}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-[#202B42] transition-colors text-left"
      >
        <span className="text-slate-400 shrink-0">
          {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-[12px] font-semibold text-slate-100 truncate">{title}</span>
            {subtitle && (
              <span className="text-[10px] font-mono text-slate-500 shrink-0">{subtitle}</span>
            )}
            {errors.length > 0 && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-semibold rounded bg-red-900/40 text-red-300 border border-red-700/60 shrink-0">
                <AlertCircle className="w-2.5 h-2.5" />
                {errors.length} {errors.length === 1 ? "eroare" : "erori"}
              </span>
            )}
            {warnings.length > 0 && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-semibold rounded bg-amber-900/40 text-amber-300 border border-amber-700/60 shrink-0">
                <AlertTriangle className="w-2.5 h-2.5" />
                {warnings.some((w) => w.kind === "COMPONENT_EMPTY")
                  ? "Componentă goală"
                  : `${warnings.length} ${warnings.length === 1 ? "avertisment" : "avertismente"}`}
              </span>
            )}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {comp.component_id ? `ID: ${comp.component_id}` : ""}
          </div>
        </div>

        {/* Cost trio */}
        <div className="hidden sm:flex items-center gap-4 text-[11px] shrink-0">
          <div className="text-right">
            <div className="text-slate-500 text-[9px] uppercase">Material</div>
            <div className="text-slate-200 font-mono tabular-nums">
              {formatNumber(comp.material_cost)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-slate-500 text-[9px] uppercase">Operații</div>
            <div className="text-slate-200 font-mono tabular-nums">
              {formatNumber(comp.operation_cost)}
            </div>
          </div>
          <div className="text-right min-w-[80px]">
            <div className="text-slate-500 text-[9px] uppercase">Total</div>
            <div className="text-slate-100 font-bold font-mono tabular-nums">
              {formatNumber(comp.total_component_cost)}
            </div>
          </div>
        </div>

        {/* Mobile: just the total */}
        <div className="sm:hidden text-right shrink-0">
          <div className="text-slate-500 text-[9px] uppercase">Total</div>
          <div className="text-slate-100 font-bold font-mono text-[12px]">
            {formatNumber(comp.total_component_cost)}
          </div>
        </div>
      </button>

      {/* Mobile: cost trio visible below header */}
      <div className="sm:hidden flex items-center justify-around gap-2 px-3 pb-2 border-t border-[#2A3548]/50 text-[10px]">
        <div className="text-center">
          <div className="text-slate-500 text-[9px] uppercase">Material</div>
          <div className="text-slate-200 font-mono tabular-nums">
            {formatNumber(comp.material_cost)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-slate-500 text-[9px] uppercase">Operații</div>
          <div className="text-slate-200 font-mono tabular-nums">
            {formatNumber(comp.operation_cost)}
          </div>
        </div>
      </div>

      {/* Expanded details */}
      {open && (
        <div id={detailsId} className="border-t border-[#2A3548] bg-[#151C2E] p-3 space-y-3">
          {/* Materials sub-table */}
          <div>
            <div className="text-[10px] font-semibold uppercase text-slate-400 mb-1.5">
              Materiale ({comp.materials_detail?.length ?? 0})
            </div>
            {comp.materials_detail && comp.materials_detail.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-[11px] min-w-[480px]">
                  <thead>
                    <tr className="text-slate-500 text-left border-b border-[#2A3548]">
                      <th className="py-1 pr-2 font-medium">Cod</th>
                      <th className="py-1 pr-2 font-medium text-right">Cantitate</th>
                      <th className="py-1 pr-2 font-medium">Unitate</th>
                      <th className="py-1 pr-2 font-medium text-right">Preț/Unitate</th>
                      <th className="py-1 font-medium text-right">Total linie</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comp.materials_detail.map((m, i) => (
                      <tr key={i} className="border-b border-[#2A3548]/50 last:border-0">
                        <td className="py-1 pr-2 font-mono text-slate-200 text-[10px]">
                          {m.material_code || m.name || "—"}
                        </td>
                        <td className="py-1 pr-2 text-slate-300 text-right tabular-nums">
                          {formatNumber(m.quantity, 2)}
                        </td>
                        <td className="py-1 pr-2 text-slate-400">{m.unit ?? "—"}</td>
                        <td className="py-1 pr-2 text-slate-300 text-right tabular-nums">
                          {formatNumber(m.unit_cost)}
                        </td>
                        <td className="py-1 text-slate-100 font-semibold text-right tabular-nums">
                          {formatNumber(m.line_total)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-[11px] text-slate-500 italic">Nu există materiale.</p>
            )}
          </div>

          {/* Operations sub-table */}
          <div>
            <div className="text-[10px] font-semibold uppercase text-slate-400 mb-1.5">
              Operații ({comp.operations_detail?.length ?? 0})
            </div>
            {comp.operations_detail && comp.operations_detail.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-[11px] min-w-[560px]">
                  <thead>
                    <tr className="text-slate-500 text-left border-b border-[#2A3548]">
                      <th className="py-1 pr-2 font-medium">Cod</th>
                      <th className="py-1 pr-2 font-medium">Centru lucru</th>
                      <th className="py-1 pr-2 font-medium text-right">Min. est.</th>
                      <th className="py-1 pr-2 font-medium text-right">Ore</th>
                      <th className="py-1 pr-2 font-medium text-right">Tarif/h</th>
                      <th className="py-1 font-medium text-right">Total linie</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comp.operations_detail.map((op, i) => (
                      <tr key={i} className="border-b border-[#2A3548]/50 last:border-0">
                        <td className="py-1 pr-2 font-mono text-slate-200 text-[10px]">
                          {op.code || op.name || "—"}
                        </td>
                        <td className="py-1 pr-2 text-slate-300">{op.workcenter ?? "—"}</td>
                        <td className="py-1 pr-2 text-slate-300 text-right tabular-nums">
                          {formatNumber(op.estimated_minutes, 0)}
                        </td>
                        <td className="py-1 pr-2 text-slate-300 text-right tabular-nums">
                          {formatNumber(op.hours, 2)}
                        </td>
                        <td className="py-1 pr-2 text-slate-300 text-right tabular-nums">
                          {formatNumber(op.rate_per_hour)}
                        </td>
                        <td className="py-1 text-slate-100 font-semibold text-right tabular-nums">
                          {formatNumber(op.line_total)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-[11px] text-slate-500 italic">Nu există operații.</p>
            )}
          </div>

          {/* Issues */}
          {hasIssues && (
            <div className="space-y-1">
              {errors.map((err, i) => (
                <div
                  key={`err-${i}`}
                  className="flex items-start gap-2 px-2 py-1 rounded border border-red-700/60 bg-red-950/30 text-red-300 text-[10px]"
                >
                  <AlertCircle className="w-3 h-3 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <span className="font-mono font-semibold">{err.kind ?? "ERROR"}</span>
                    {err.path && <span className="text-red-400/80"> @ {err.path}</span>}
                    {err.detail && <span className="text-red-200/90">: {err.detail}</span>}
                  </div>
                </div>
              ))}
              {warnings.map((w, i) => (
                <div
                  key={`warn-${i}`}
                  className="flex items-start gap-2 px-2 py-1 rounded border border-amber-700/60 bg-amber-950/30 text-amber-300 text-[10px]"
                >
                  <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <span className="font-mono font-semibold">{w.kind ?? "WARNING"}</span>
                    {w.path && <span className="text-amber-400/80"> @ {w.path}</span>}
                    {w.detail && <span className="text-amber-200/90">: {w.detail}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ComponentBreakdownTable({
  components,
}: ComponentBreakdownTableProps) {
  if (!components || components.length === 0) {
    // Defensive: parent should already have filtered this case, but stay
    // robust — render nothing instead of crashing.
    return null;
  }

  // Sum totals from the breakdown for a footer. This is NOT a computation
  // — it's just addition of already-computed values for display. The
  // commercial / VAT math still lives in the "Pricing Summary" panel,
  // which is separate.
  const totalMaterial = components.reduce(
    (acc, c) => acc + Number(c.material_cost ?? 0),
    0,
  );
  const totalOperation = components.reduce(
    (acc, c) => acc + Number(c.operation_cost ?? 0),
    0,
  );
  const totalCost = components.reduce(
    (acc, c) => acc + Number(c.total_component_cost ?? 0),
    0,
  );

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-[10px] text-slate-500 px-1">
        <span>{components.length} {components.length === 1 ? "componentă" : "componente"}</span>
        <span className="italic">Apasă pe rând pentru detalii</span>
      </div>

      <div className="space-y-1.5">
        {components.map((c, i) => (
          <ComponentRow key={c.component_id ?? `cmp-${i}`} comp={c} index={i} />
        ))}
      </div>

      {/* Footer totals — sum of the already-calculated values */}
      <div className="flex items-center justify-between gap-4 px-3 py-2 rounded-lg bg-[#0F1624] border border-[#2A3548] text-[11px]">
        <span className="text-slate-400 font-semibold uppercase text-[10px]">
          Total componente
        </span>
        <div className="flex items-center gap-4 font-mono tabular-nums">
          <div className="text-right">
            <div className="text-slate-500 text-[9px] uppercase">Material</div>
            <div className="text-slate-200">{formatNumber(totalMaterial)}</div>
          </div>
          <div className="text-right">
            <div className="text-slate-500 text-[9px] uppercase">Operații</div>
            <div className="text-slate-200">{formatNumber(totalOperation)}</div>
          </div>
          <div className="text-right min-w-[80px]">
            <div className="text-slate-500 text-[9px] uppercase">Total</div>
            <div className="text-slate-100 font-bold">{formatNumber(totalCost)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}