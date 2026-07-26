import type { IntakeV6OperatorWorkSummaryCounts } from "@/lib/intakeV6/intakeV6ConfirmSummary";
import { v6 } from "./atoms/intakeV6Presentation";

export const INTAKE_V6_VECTOR_PRODUCTION_PARTS_LABEL =
  "Piese vectoriale de producție detectate";
export const INTAKE_V6_VECTOR_PRODUCTION_PARTS_HINT =
  "Acest număr vine din geometria SVG și nu reprezintă numărul de caractere vizibile din text.";
export const INTAKE_V6_NO_OCR_NOTE =
  "Aplicația nu folosește OCR și nu ghicește numărul de caractere vizibile. Pentru fișiere convertite în curbe, sunt raportate piese vectoriale, nu text editabil.";

function fmtCount(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return String(value);
}

export default function IntakeV6OperatorWorkSummaryTechnicalDetails({
  counts,
  testId = "intake-v6-operator-work-summary-technical",
}: {
  counts: Pick<IntakeV6OperatorWorkSummaryCounts, "productionParts">;
  testId?: string;
}) {
  return (
    <div className={`${v6.card} mb-4`} data-testid={testId}>
      <h3 className="mb-2 text-[12px] font-bold uppercase tracking-wide">Contoare geometrie</h3>
      <dl className="grid gap-0 text-[12px]">
        <div className="flex justify-between gap-4 border-b border-wo-border-strong py-2">
          <dt className="text-slate-500" title={INTAKE_V6_VECTOR_PRODUCTION_PARTS_HINT}>
            {INTAKE_V6_VECTOR_PRODUCTION_PARTS_LABEL}
          </dt>
          <dd className={v6.mono} data-testid={`${testId}-production-parts`}>
            {fmtCount(counts.productionParts)}
          </dd>
        </div>
      </dl>
      <p className="mt-3 text-[10px] text-slate-500" data-testid={`${testId}-no-ocr-note`}>
        {INTAKE_V6_NO_OCR_NOTE}
      </p>
    </div>
  );
}



