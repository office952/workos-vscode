import { FileCheck, Layers, Ruler } from "lucide-react";
import { formatFaceBackPrepMoney } from "@/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay";
import { COST_INTERN_ESTIMATIV_LABEL } from "@/lib/intakeV6/intakeV6OfferCostChromeVocabulary";
import { v6 } from "./atoms/intakeV6Presentation";

function KpiCell({
  icon: Icon,
  label,
  value,
  testId,
  highlight = false,
}: {
  icon: typeof FileCheck;
  label: string;
  value: string;
  testId: string;
  highlight?: boolean;
}) {
  return (
    <div
      className="flex min-w-0 flex-1 items-center gap-2 rounded border border-wo-border-strong/80 bg-wo-surface-raised/60 px-2.5 py-2"
      data-testid={testId}
    >
      <Icon className="h-3.5 w-3.5 shrink-0 text-cyan-400/80" aria-hidden />
      <div className="min-w-0">
        <span className={`block ${v6.metricLabel}`}>{label}</span>
        <span
          className={`block truncate tabular-nums ${highlight ? "text-[15px] font-bold text-emerald-300" : "text-[12px] font-semibold text-slate-100"}`}
        >
          {value}
        </span>
      </div>
    </div>
  );
}

export default function IntakeV6ConfirmKpiStrip({
  internalCostEur,
  internalCurrency = "EUR",
  widthMm,
  heightMm,
  layerCount,
  loading = false,
}: {
  internalCostEur: number | null;
  internalCurrency?: string;
  widthMm?: number | null;
  heightMm?: number | null;
  layerCount?: number | null;
  loading?: boolean;
}) {
  const dimensions =
    widthMm != null && heightMm != null && Number.isFinite(widthMm) && Number.isFinite(heightMm)
      ? `${Math.round(widthMm)}×${Math.round(heightMm)} mm`
      : "—";

  return (
    <div
      className="flex flex-wrap gap-2 rounded-md border border-wo-border-strong/90 bg-wo-surface-inset/80 p-2"
      data-testid="intake-v6-confirm-kpi-strip"
    >
      <KpiCell
        icon={FileCheck}
        label={COST_INTERN_ESTIMATIV_LABEL}
        value={
          loading || internalCostEur == null
            ? "—"
            : formatFaceBackPrepMoney(internalCostEur, internalCurrency)
        }
        testId="intake-v6-confirm-kpi-internal"
      />
      <KpiCell
        icon={Ruler}
        label="Dimensiune"
        value={loading ? "…" : dimensions}
        testId="intake-v6-confirm-kpi-dimensions"
      />
      <KpiCell
        icon={Layers}
        label="Straturi"
        value={loading ? "…" : layerCount != null ? String(layerCount) : "—"}
        testId="intake-v6-confirm-kpi-layers"
      />
    </div>
  );
}
