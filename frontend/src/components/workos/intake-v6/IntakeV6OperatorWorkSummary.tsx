import type { IntakeV6OperatorWorkSummaryCounts } from "@/lib/intakeV6/intakeV6ConfirmSummary";
import { v6 } from "./atoms/intakeV6Presentation";

function fmtCount(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return String(value);
}

export default function IntakeV6OperatorWorkSummary({
  counts,
  layerCount,
  testId = "intake-v6-operator-work-summary",
}: {
  counts: IntakeV6OperatorWorkSummaryCounts;
  layerCount?: number | null;
  testId?: string;
}) {
  return (
    <div className={`${v6.card} mb-4`} data-testid={testId}>
      <h3 className="mb-2 text-[12px] font-bold uppercase tracking-wide">Rezumat lucrare</h3>
      <dl className="grid gap-0 text-[12px]">
        <div className="flex justify-between gap-4 border-b border-[#2A3548] py-2">
          <dt
            className="text-slate-500"
            title="Layere confirmate ca litere volumetrice in lucrare."
          >
            Vector Litere
          </dt>
          <dd className={v6.mono} data-testid={`${testId}-volumetric-letters`}>
            {fmtCount(counts.productionParts)}
          </dd>
        </div>
        <div className="flex justify-between gap-4 border-b border-[#2A3548] py-2">
          <dt
            className="text-slate-500"
            title="Elemente confirmate ca emblemă/logo."
          >
            Vector Atipic
          </dt>
          <dd className={v6.mono} data-testid={`${testId}-emblem-count`}>
            {fmtCount(counts.artworkCount)}
          </dd>
        </div>
        <div className="flex justify-between gap-4 border-b border-[#2A3548] py-2">
          <dt
            className="text-slate-500"
            title="Total piese luate în calcul pentru preview: piese producție + artwork."
          >
            Piese plasate în layout
          </dt>
          <dd className={v6.mono} data-testid={`${testId}-layout-parts`}>
            {fmtCount(counts.layoutPartsCount)}
          </dd>
        </div>
        <div className="flex justify-between gap-4 py-2">
          <dt className="text-slate-500" title="Straturi SVG detectate în fișierul sursă.">
            Layere SVG
          </dt>
          <dd className={v6.mono} data-testid={`${testId}-layers`}>
            {fmtCount(layerCount)}
          </dd>
        </div>
      </dl>
    </div>
  );
}



