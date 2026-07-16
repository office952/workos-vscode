import type { ReactNode } from "react";
import {
  FileCheck,
  Layers,
  Lightbulb,
  Ruler,
} from "lucide-react";
import type {
  IntakeV6NestingPreviewResponse,
  IntakeV6QuoteHandoffPreviewResponse,
} from "@/lib/intakeV6/intakeV6Api";
import type { IntakeV6ConfirmSummaryViewModel } from "@/lib/intakeV6/intakeV6ConfirmSummary";
import { collectArtworkUndecidedWarnings } from "@/lib/intakeV6/intakeV6QuoteHandoffReadiness";
import { formatConfirmSummaryM, formatConfirmSummaryM2 } from "@/lib/intakeV6/intakeV6ConfirmSummary";
import { v6 } from "./atoms/intakeV6Presentation";

function NestingMiniThumb({ preview }: { preview: IntakeV6NestingPreviewResponse }) {
  const activeSheet = preview.sheets.find((sheet) => sheet.is_active_for_breakdown) ?? preview.sheets[0];
  if (!activeSheet) return null;
  const width = activeSheet.sheet_width_mm ?? 1000;
  const height = activeSheet.sheet_length_mm ?? 1000;
  const scale = Math.min(240 / width, 120 / height);
  const viewW = width * scale;
  const viewH = height * scale;
  const sheetParts = preview.parts.filter(
    (part) => part.nesting_target === `sheet:${activeSheet.config_id}`,
  );

  return (
    <div className={`${v6.cardCompact} !p-2`} data-testid="intake-v6-confirm-nesting-compact">
      <p className="mb-1 text-[10px] font-semibold text-slate-400">Nesting activ</p>
      <svg
        width={viewW}
        height={viewH}
        viewBox={`0 0 ${width} ${height}`}
        className="mx-auto max-w-full border border-[#2A3548] bg-[#0B1220]"
        data-testid="intake-v6-confirm-nesting-thumb"
      >
        <rect x={0} y={0} width={width} height={height} fill="#111827" stroke="#334155" strokeWidth={2} />
        {sheetParts.map((part, index) => {
          const x = part.placement_x_mm ?? index * 20;
          const y = part.placement_y_mm ?? index * 10;
          const w = part.bounds_width_mm ?? 10;
          const h = part.bounds_height_mm ?? 10;
          return (
            <rect
              key={part.part_id}
              x={x}
              y={y}
              width={w}
              height={h}
              fill="#00984655"
              stroke="#94a3b8"
              strokeWidth={1}
            />
          );
        })}
      </svg>
      <p className="mt-1 text-center text-[9px] text-slate-500">
        {activeSheet.placement_count} piese ·{" "}
        {activeSheet.efficiency_percent != null
          ? `${activeSheet.efficiency_percent.toFixed(0)}% eff`
          : "preview"}
      </p>
    </div>
  );
}

function Tile({
  icon: Icon,
  title,
  testId,
  children,
}: {
  icon: typeof FileCheck;
  title: string;
  testId: string;
  children: ReactNode;
}) {
  return (
    <div className={`${v6.cardCompact} !p-3`} data-testid={testId}>
      <div className="mb-2 flex items-center gap-1.5">
        <Icon className="h-3.5 w-3.5 text-cyan-400/80" aria-hidden />
        <h3 className="text-[11px] font-semibold text-slate-200">{title}</h3>
      </div>
      <div className="space-y-1.5 text-[11px] text-slate-300">{children}</div>
    </div>
  );
}

function buildFinishSummaryLine(summary: IntakeV6ConfirmSummaryViewModel): string {
  const parts: string[] = [];
  if (summary.finish.letterRows.length > 0) {
    parts.push(
      `${summary.finish.letterRows.length} strat${summary.finish.letterRows.length === 1 ? "" : "e"} litere`,
    );
  } else if (summary.finish.letterFaceLabel) {
    parts.push(`Față ${summary.finish.letterFaceLabel}`);
  }
  if (summary.finish.artworkRows.length > 0) {
    parts.push(`${summary.finish.artworkRows.length} Vector Logo`);
  }
  if (summary.finish.vinylFace && summary.finish.vinylFace !== "—") {
    parts.push(summary.finish.vinylFace);
  }
  if (summary.lighting.illuminated) {
    parts.push("LED");
  }
  parts.push(summary.finish.backingForex);
  return parts.filter(Boolean).join(" · ") || "—";
}

export default function IntakeV6ConfirmDashboard({
  workspaceCode,
  templateLabel,
  svgFileName,
  summary,
  handoffPreview,
  fatalBlockers,
  reviewWarnings,
  nestingPreview,
  loading = false,
}: {
  workspaceCode?: string | null;
  templateLabel?: string | null;
  svgFileName?: string | null;
  summary: IntakeV6ConfirmSummaryViewModel;
  handoffPreview: IntakeV6QuoteHandoffPreviewResponse | null;
  fatalBlockers: string[];
  reviewWarnings: string[];
  nestingPreview: IntakeV6NestingPreviewResponse | null;
  loading?: boolean;
}) {
  const artworkWarnings = collectArtworkUndecidedWarnings(reviewWarnings);
  const finishLine = buildFinishSummaryLine(summary);
  const recapNote = loading
    ? "Verific…"
    : fatalBlockers.length > 0 || artworkWarnings.length > 0
      ? "Revizuiește observațiile din statusul de configurare."
      : handoffPreview?.operator_confirmation_complete === false
        ? "Confirmă draftul intern în secțiunea de mai jos."
        : "Recapitulare produs și geometrie.";

  return (
    <div className="space-y-3" data-testid="intake-v6-confirm-dashboard-tiles">
      <div className="grid gap-3 lg:grid-cols-3">
        <Tile icon={FileCheck} title="Recapitulare" testId="intake-v6-confirm-tile-verdict">
          <p className="text-[11px] leading-relaxed text-slate-400" data-testid="intake-v6-confirm-tile-recap-note">
            {recapNote}
          </p>
        </Tile>

        <Tile icon={Layers} title="Lucrare" testId="intake-v6-confirm-tile-work">
          <p>
            <span className="text-slate-500">Cerere </span>
            <span className={v6.mono}>{workspaceCode ?? "—"}</span>
          </p>
          <p>
            <span className="text-slate-500">Șablon </span>
            {templateLabel ?? "—"}
          </p>
          <p className="truncate" title={svgFileName ?? undefined}>
            <span className="text-slate-500">SVG </span>
            <span className={v6.mono} data-testid="intake-v6-confirm-svg-file">
              {svgFileName ?? "—"}
            </span>
          </p>
          <p>
            <span className="text-slate-500">Straturi </span>
            {summary.structure.layerCount}
            {summary.structure.realLettersCount != null
              ? ` · ${summary.structure.realLettersCount} litere`
              : ""}
          </p>
        </Tile>

        <Tile icon={Ruler} title="Geometrie" testId="intake-v6-confirm-tile-geometry">
          <p data-testid="intake-v6-confirm-gross-area">
            <span className="text-slate-500">Dimensiune </span>
            {summary.geometry.grossFaceAreaM2 != null
              ? formatConfirmSummaryM2(summary.geometry.grossFaceAreaM2)
              : "—"}
          </p>
          <p data-testid="intake-v6-confirm-return-perimeter">
            <span className="text-slate-500">Cant total </span>
            {formatConfirmSummaryM(summary.geometry.returnPerimeterM)}
          </p>
          <p data-testid="intake-v6-confirm-led-perimeter">
            <span className="inline-flex items-center gap-1">
              <Lightbulb className="h-3 w-3 text-amber-300/80" aria-hidden />
              LED {formatConfirmSummaryM(summary.geometry.ledPerimeterM)}
            </span>
          </p>
          <p data-testid="intake-v6-confirm-plexiglas-area">
            <span className="text-slate-500">Plexi nesting </span>
            {formatConfirmSummaryM2(summary.geometry.quoteablePlexiglasM2)}
          </p>
        </Tile>
      </div>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(220px,280px)]">
        <div className={`${v6.cardCompact} !p-3`} data-testid="intake-v6-confirm-finish-compact">
          <h3 className="mb-1.5 text-[11px] font-semibold text-slate-200">Finisaje — rezumat</h3>
          <p className="text-[11px] leading-relaxed text-slate-300">{finishLine}</p>
        </div>

        {nestingPreview ? (
          <NestingMiniThumb preview={nestingPreview} />
        ) : (
          <div className={`${v6.cardCompact} flex !p-3 items-center justify-center`}>
            <p className="text-[10px] text-slate-500">Nesting preview…</p>
          </div>
        )}
      </div>
    </div>
  );
}
