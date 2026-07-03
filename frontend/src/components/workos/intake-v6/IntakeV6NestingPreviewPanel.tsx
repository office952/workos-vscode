import { useMemo, useState } from "react";
import type { IntakeV6NestingPreviewResponse } from "@/lib/intakeV6/intakeV6Api";
import { v6 } from "./atoms/intakeV6Presentation";

function SheetCanvas({
  sheet,
  parts,
}: {
  sheet: IntakeV6NestingPreviewResponse["sheets"][number];
  parts: IntakeV6NestingPreviewResponse["parts"];
}) {
  const width = sheet.sheet_width_mm ?? 1000;
  const height = sheet.sheet_length_mm ?? 1000;
  const scale = Math.min(520 / width, 280 / height);
  const viewW = width * scale;
  const viewH = height * scale;

  const sheetParts = parts.filter((p) => p.nesting_target === `sheet:${sheet.config_id}`);

  return (
    <svg
      width={viewW}
      height={viewH}
      viewBox={`0 0 ${width} ${height}`}
      className="max-w-full border border-[#2A3548] bg-[#0B1220]"
      data-testid={`intake-v6-nesting-canvas-${sheet.config_id}`}
    >
      <rect x={0} y={0} width={width} height={height} fill="#111827" stroke="#334155" strokeWidth={2} />
      {sheetParts.map((part, index) => {
        const x = part.placement_x_mm ?? index * 20;
        const y = part.placement_y_mm ?? index * 10;
        const w = part.bounds_width_mm ?? 10;
        const h = part.bounds_height_mm ?? 10;
        const fill =
          part.layer_role === "face"
            ? "#00984655"
            : part.layer_role === "printed_artwork"
              ? "#6366f155"
              : part.material_intent === "backing"
                ? "#f59e0b55"
                : "#64748b55";
        return (
          <g key={part.part_id}>
            <rect x={x} y={y} width={w} height={h} fill={fill} stroke="#94a3b8" strokeWidth={1} />
            <text x={x + 4} y={y + 14} fill="#e2e8f0" fontSize={Math.max(10, Math.min(w, h) / 8)}>
              {part.part_id.slice(0, 12)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function ActiveSheetLayout({
  sheet,
  parts,
}: {
  sheet: IntakeV6NestingPreviewResponse["sheets"][number];
  parts: IntakeV6NestingPreviewResponse["parts"];
}) {
  return (
    <div
      className="rounded border border-emerald-500/30 bg-emerald-500/5 p-3"
      data-testid={`intake-v6-nesting-active-sheet-${sheet.config_id}`}
    >
      <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px]">
        <strong className="text-emerald-200">{sheet.display_label}</strong>
        <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] text-emerald-200">
          Layout activ pentru calcul intern Material Breakdown
        </span>
        {sheet.efficiency_percent != null ? (
          <span className="text-slate-500">{sheet.efficiency_percent.toFixed(1)}% eff (bbox)</span>
        ) : null}
      </div>
      <dl className="mb-2 grid gap-1 text-[10px] text-slate-400 sm:grid-cols-2">
        <div>
          Aria plăcii disponibile: {sheet.used_sheet_area_sqm?.toFixed(3) ?? "—"} m² — nu este consum
          ofertat automat
        </div>
        <div>Piese plasate în layout: {sheet.placement_count}</div>
        <div>Material target: {sheet.material_target ?? "—"}</div>
        <div>{sheet.breakdown_note ?? "Folosit pentru Material Breakdown"}</div>
      </dl>
      <p className="mb-2 text-[10px] text-amber-200/90">
        Preview diagnostic: nu consumă stoc și nu reprezintă toolpath real.
      </p>
      <SheetCanvas sheet={sheet} parts={parts} />
    </div>
  );
}

function AlternativeSheetRow({
  sheet,
}: {
  sheet: IntakeV6NestingPreviewResponse["sheets"][number];
}) {
  return (
    <div
      className="rounded border border-[#2A3548]/80 p-2 text-[10px] text-slate-400"
      data-testid={`intake-v6-nesting-alt-sheet-${sheet.config_id}`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <strong className="text-slate-300">{sheet.display_label}</strong>
        <span className="text-slate-500">Variantă alternativă — nu intră în Material Breakdown</span>
      </div>
      <div className="mt-1 grid gap-1 sm:grid-cols-2">
        <span>
          Aria plăcii disponibile: {sheet.used_sheet_area_sqm?.toFixed(3) ?? "—"} m² (preview)
        </span>
        <span>Piese plasate: {sheet.placement_count}</span>
      </div>
    </div>
  );
}

export default function IntakeV6NestingPreviewPanel({
  preview,
}: {
  preview: IntakeV6NestingPreviewResponse | null | undefined;
}) {
  const [open, setOpen] = useState(false);
  const [alternativesOpen, setAlternativesOpen] = useState(false);

  const { activeSheets, alternativeSheets, activeRolls, alternativeRolls } = useMemo(() => {
    if (!preview) {
      return {
        activeSheets: [] as IntakeV6NestingPreviewResponse["sheets"],
        alternativeSheets: [] as IntakeV6NestingPreviewResponse["sheets"],
        activeRolls: [] as IntakeV6NestingPreviewResponse["rolls"],
        alternativeRolls: [] as IntakeV6NestingPreviewResponse["rolls"],
      };
    }
    return {
      activeSheets: preview.sheets.filter((s) => s.is_active_for_breakdown),
      alternativeSheets: preview.sheets.filter((s) => !s.is_active_for_breakdown),
      activeRolls: preview.rolls.filter((r) => r.is_active_for_breakdown),
      alternativeRolls: preview.rolls.filter((r) => !r.is_active_for_breakdown),
    };
  }, [preview]);

  if (!preview) return null;

  const partsInActiveLayout = preview.parts.filter((p) =>
    activeSheets.some((s) => p.nesting_target === `sheet:${s.config_id}`),
  );

  return (
    <div className="mt-4 border-t border-[#2A3548] pt-4" data-testid="intake-v6-nesting-preview">
      <button
        type="button"
        className="mb-2 flex w-full items-center justify-between text-left text-[11px] font-bold uppercase tracking-wide text-slate-400"
        onClick={() => setOpen((v) => !v)}
        data-testid="intake-v6-nesting-preview-toggle"
      >
        <span>A. Preview nesting — diagnostic (nu consum stoc)</span>
        <span>{open ? "▾" : "▸"}</span>
      </button>

      {open ? (
        <div className="space-y-4">
          <p className="text-[10px] text-amber-200" data-testid="intake-v6-nesting-preview-disclaimer">
            {preview.disclaimer}
          </p>

          <section data-testid="intake-v6-nesting-summary-section">
            <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-500">
              1. Rezumat nesting
            </h4>
            <dl
              className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 sm:grid-cols-4"
              data-testid="intake-v6-nesting-preview-summary"
            >
              <div>
                <dt className="text-slate-500">Variante placă simulate</dt>
                <dd className="text-slate-200">{preview.summary.sheet_layouts}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Variante rolă simulate</dt>
                <dd className="text-slate-200">{preview.summary.roll_layouts}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Layout-uri active (breakdown)</dt>
                <dd className="text-slate-200">
                  {preview.summary.active_sheet_layouts + preview.summary.active_roll_layouts}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Layout-uri alternative</dt>
                <dd className="text-slate-200">{preview.summary.alternative_layouts}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Piese în layout activ</dt>
                <dd className="text-slate-200">{preview.summary.nestable_parts}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Găuri excluse</dt>
                <dd className="text-slate-200">{preview.summary.holes_excluded}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Artwork exclus</dt>
                <dd className="text-slate-200">{preview.summary.artwork_parts}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Avertismente</dt>
                <dd className="text-slate-200">{preview.warnings.length}</dd>
              </div>
            </dl>
          </section>

          {preview.warnings.length > 0 ? (
            <ul className="space-y-1 text-[10px] text-slate-400" data-testid="intake-v6-nesting-warnings">
              {preview.warnings.map((w) => (
                <li key={w.code}>• {w.message}</li>
              ))}
            </ul>
          ) : null}

          {activeSheets.length > 0 ? (
            <section>
              <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-500">
                2. Layout activ pentru material
              </h4>
              <div className="space-y-3">
                {activeSheets.map((sheet) => (
                  <ActiveSheetLayout key={sheet.config_id} sheet={sheet} parts={preview.parts} />
                ))}
              </div>
            </section>
          ) : null}

          {alternativeSheets.length > 0 || alternativeRolls.length > 0 ? (
            <section>
              <button
                type="button"
                className="mb-2 flex w-full items-center justify-between text-left text-[11px] font-bold uppercase tracking-wide text-slate-500"
                onClick={() => setAlternativesOpen((v) => !v)}
                data-testid="intake-v6-nesting-alternatives-toggle"
              >
                <span>3. Layout-uri alternative ({alternativeSheets.length + alternativeRolls.length})</span>
                <span>{alternativesOpen ? "▾" : "▸"}</span>
              </button>
              {alternativesOpen ? (
                <div className="space-y-2">
                  <p className="text-[10px] text-slate-500">
                    Variantă alternativă — nu intră în Material Breakdown. Doar comparație diagnostic.
                  </p>
                  {alternativeSheets.map((sheet) => (
                    <AlternativeSheetRow key={sheet.config_id} sheet={sheet} />
                  ))}
                  {alternativeRolls.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-[10px]">
                        <thead>
                          <tr className="border-b border-[#2A3548] text-left text-slate-500">
                            <th className="py-1 pr-2">Layer</th>
                            <th className="py-1 pr-2">Roll mm</th>
                            <th className="py-1">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {alternativeRolls.map((job, idx) => (
                            <tr
                              key={`${job.roll_config_id}-${job.source_layer_name}-${idx}`}
                              className="border-b border-[#2A3548]/50"
                            >
                              <td className="py-1 pr-2">{job.source_layer_name ?? "—"}</td>
                              <td className="py-1 pr-2">{job.roll_width_mm ?? "—"}</td>
                              <td className="py-1 text-slate-500">Variantă alternativă</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </section>
          ) : null}

          {activeRolls.length > 0 ? (
            <div>
              <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-500">
                Rolă activă (breakdown)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-[10px]">
                  <thead>
                    <tr className="border-b border-[#2A3548] text-left text-slate-500">
                      <th className="py-1 pr-2">Layer</th>
                      <th className="py-1 pr-2">Role</th>
                      <th className="py-1 pr-2">Roll mm</th>
                      <th className="py-1 pr-2">Area m²</th>
                      <th className="py-1">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeRolls.map((job, idx) => (
                      <tr
                        key={`${job.roll_config_id}-${job.source_layer_name}-${idx}`}
                        className="border-b border-[#2A3548]/50"
                      >
                        <td className="py-1 pr-2">{job.source_layer_name ?? "—"}</td>
                        <td className="py-1 pr-2">{job.layer_role ?? "—"}</td>
                        <td className="py-1 pr-2">{job.roll_width_mm ?? "—"}</td>
                        <td className="py-1 pr-2">{job.used_roll_area_sqm?.toFixed(4) ?? "—"}</td>
                        <td className="py-1 text-emerald-300">Layout activ breakdown</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {partsInActiveLayout.length > 0 ? (
            <div>
              <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-500">
                Piese în layout activ
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-[10px]" data-testid="intake-v6-nesting-parts-table">
                  <thead>
                    <tr className="border-b border-[#2A3548] text-left text-slate-500">
                      <th className="py-1 pr-2">partId</th>
                      <th className="py-1 pr-2">Layer</th>
                      <th className="py-1 pr-2">Role</th>
                      <th className="py-1 pr-2">Area m²</th>
                      <th className="py-1">În Material Breakdown</th>
                    </tr>
                  </thead>
                  <tbody>
                    {partsInActiveLayout.map((part) => (
                      <tr key={part.part_id} className="border-b border-[#2A3548]/50">
                        <td className={`py-1 pr-2 ${v6.mono}`}>{part.part_id}</td>
                        <td className="py-1 pr-2">{part.source_layer_name ?? "—"}</td>
                        <td className="py-1 pr-2">{part.layer_role ?? "—"}</td>
                        <td className="py-1 pr-2">{part.area_sqm?.toFixed(4) ?? "—"}</td>
                        <td className="py-1">{part.counted_in_material_lines.join(", ") || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {preview.material_traces.length > 0 ? (
            <div>
              <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-500">
                Ce intră în Material Breakdown (trace)
              </h4>
              <ul className="space-y-2 text-[10px] text-slate-300">
                {preview.material_traces.map((trace) => (
                  <li key={trace.material_key} data-testid={`intake-v6-nesting-trace-${trace.material_key}`}>
                    <strong>{trace.display_name}</strong>: {trace.reported_quantity.toFixed(4)} {trace.unit}
                    {trace.uses_placement_footprint ? " · bazat pe placement bbox" : ""}
                    {trace.uses_full_sheet_stock_proration ? " · proratare placă întreagă" : ""}
                    {trace.source_part_ids.length > 0 ? (
                      <span className="block text-slate-500">piese: {trace.source_part_ids.join(", ")}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}



