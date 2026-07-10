import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { CheckCircle2, CircleDashed, Layers, Loader2 } from "lucide-react";
import IntakeV6Nest2SvgUploader from "./IntakeV6Nest2SvgUploader";
import IntakeV6LayersColorBreakdown, { isSingleLayerColorMode } from "./IntakeV6LayersColorBreakdown";
import IntakeV6LayersWarningsPanel from "./IntakeV6LayersWarningsPanel";
import { ARTWORK_ONLY_STEP1_MESSAGE } from "@/lib/intakeV6/intakeV6ArtworkOnlyGuard";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6LayersOperatorPanel({
  analyzing,
  canImportSvg,
  workspaceReady,
  report,
  confirmation,
  layerStats,
  parseWarning,
  scopeWarnings,
  artworkOnlyRequiresDecision = false,
  onImportFile,
  onConfirmAllRoles,
  onScrollToPending,
  onJumpToLayer,
}: {
  analyzing: boolean;
  canImportSvg: boolean;
  workspaceReady: boolean;
  report: SvgAnalysisCoreReport | null;
  confirmation: LayerRoleConfirmation | null;
  layerStats: { total: number; confirmed: number; pending: number };
  parseWarning?: string | null;
  scopeWarnings: string[];
  artworkOnlyRequiresDecision?: boolean;
  onImportFile: (file: File) => void | Promise<void>;
  onConfirmAllRoles: () => void;
  onScrollToPending?: () => void;
  onJumpToLayer?: (layerKey: string) => void;
}) {
  const showColorBreakdown = report != null && isSingleLayerColorMode(report);
  const progressPct =
    layerStats.total > 0 ? Math.round((layerStats.confirmed / layerStats.total) * 100) : 0;

  const statusTone =
    confirmation?.confirmationStatus === "complete"
      ? "ok"
      : analyzing
        ? "pending"
        : report
          ? "action"
          : "muted";

  const statusLabel = analyzing
    ? "Analiză în curs"
    : confirmation?.confirmationStatus === "complete"
      ? "Straturi confirmate"
      : report
        ? "Confirmare necesară"
        : "Fără analiză";

  return (
    <aside
      className="flex min-w-0 flex-col gap-4 lg:sticky lg:top-3 lg:self-start"
      data-testid="intake-v6-layers-operator-panel"
    >
      <div className={`${v6.cardCompact} space-y-3`}>
        <div>
          <h2 className={v6.screenTitle}>Panou operator</h2>
          <p className={v6.sectionDesc}>
            Upload, status analiză și acțiuni rapide pentru confirmarea straturilor.
          </p>
        </div>

        <div>
          <h3 className={v6.sectionTitle}>Rezumat straturi</h3>
        </div>

        <div className="flex flex-col gap-2">
          {report && confirmation && confirmation.confirmationStatus !== "complete" ? (
            <button
              type="button"
              className={`${v6.btnConfirm} inline-flex w-full items-center justify-center gap-2`}
              onClick={onConfirmAllRoles}
              data-testid="intake-v6-confirm-all-roles"
            >
              <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden />
              {artworkOnlyRequiresDecision ? "Confirmă logo/vector" : "Confirmă toate sugestiile"}
              {layerStats.pending > 0 ? (
                <span className="rounded-full bg-white/20 px-1.5 py-0.5 text-[11px] font-bold tabular-nums">
                  {layerStats.pending}
                </span>
              ) : null}
            </button>
          ) : report && confirmation?.confirmationStatus === "complete" ? (
            <div
              className="flex w-full items-center justify-center gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-[12px] font-semibold text-emerald-300"
              data-testid="intake-v6-layers-all-confirmed"
            >
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" aria-hidden />
              Toate straturile confirmate
            </div>
          ) : null}

          {artworkOnlyRequiresDecision ? (
            <p
              className="rounded border border-amber-500/30 bg-amber-500/10 px-2.5 py-2 text-[11px] leading-relaxed text-amber-100/90"
              data-testid="intake-v6-artwork-only-operator-hint"
            >
              {ARTWORK_ONLY_STEP1_MESSAGE} Confirmă vectorul constructiv sau reîncarcă un fișier cu straturi separate.
            </p>
          ) : null}

          <IntakeV6Nest2SvgUploader
            busy={analyzing}
            disabled={!canImportSvg}
            label="Încarcă SVG"
            busyLabel="Analizez..."
            buttonClassName={
              report && confirmation && confirmation.confirmationStatus !== "complete"
                ? `${v6.btnGhost} w-full`
                : v6.btnPrimary
            }
            onFileSelected={(file) => void onImportFile(file)}
          />
        </div>

        {!workspaceReady ? (
          <p className={v6.helper} data-testid="intake-v6-workspace-bootstrap-pending">
            Pregătesc workspace-ul V6...
          </p>
        ) : null}

        {report && confirmation && confirmation.confirmationStatus !== "complete" ? (
          <div className="flex flex-wrap items-center gap-2">
            <span data-testid="intake-v6-layers-status-badge">
              <AtomsBadge tone={statusTone}>
                {analyzing ? (
                  <span className="inline-flex items-center gap-1">
                    <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
                    {statusLabel}
                  </span>
                ) : (
                  statusLabel
                )}
              </AtomsBadge>
            </span>
          </div>
        ) : null}

        {report && confirmation ? (
          <div
            className="rounded-lg border border-[#2A3548]/70 bg-[#0A0F1A]/45 p-2.5"
            data-testid="intake-v6-layers-confirmation-summary"
          >
            <div className={`mb-2 flex items-center justify-between gap-2 ${v6.metricLabel}`}>
              <span>Progres confirmare</span>
              <span className="font-semibold tabular-nums text-slate-300">{progressPct}%</span>
            </div>
            <div className="mb-2 h-1.5 overflow-hidden rounded-full bg-slate-800/90">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-600/80 to-emerald-400/90 transition-all"
                style={{ width: `${progressPct}%` }}
                data-testid="intake-v6-layers-confirmation-progress"
              />
            </div>
            <div className="grid grid-cols-3 gap-1.5 text-center">
              <div
                className="rounded-md border border-[#2A3548]/60 bg-[#111827]/60 px-1 py-1.5"
                title="Straturi detectate"
              >
                <Layers className="mx-auto h-3.5 w-3.5 text-slate-400" aria-hidden />
                <strong className="mt-0.5 block text-[13px] tabular-nums text-slate-100">
                  {layerStats.total}
                </strong>
                <span className="sr-only">Detectate</span>
              </div>
              <div
                className="rounded-md border border-emerald-500/20 bg-emerald-500/5 px-1 py-1.5"
                title="Straturi confirmate"
              >
                <CheckCircle2 className="mx-auto h-3.5 w-3.5 text-emerald-400" aria-hidden />
                <strong className="mt-0.5 block text-[13px] tabular-nums text-emerald-300">
                  {layerStats.confirmed}
                </strong>
                <span className="sr-only">Confirmate</span>
              </div>
              <div
                className="rounded-md border border-amber-500/20 bg-amber-500/5 px-1 py-1.5"
                title="Straturi de confirmat"
              >
                <CircleDashed className="mx-auto h-3.5 w-3.5 text-amber-400" aria-hidden />
                <strong className="mt-0.5 block text-[13px] tabular-nums text-amber-300">
                  {layerStats.pending}
                </strong>
                <span className="sr-only">De confirmat</span>
              </div>
            </div>
          </div>
        ) : null}

        {layerStats.pending > 0 && onScrollToPending ? (
          <button
            type="button"
            className={`${v6.btnGhost} w-full`}
            onClick={onScrollToPending}
            data-testid="intake-v6-layers-jump-pending"
          >
            Mergi la straturi neconfirmate
          </button>
        ) : null}
      </div>

      <IntakeV6LayersWarningsPanel
        report={report}
        confirmation={confirmation}
        parseWarning={parseWarning}
        scopeWarnings={scopeWarnings}
        onJumpToLayer={onJumpToLayer}
      />

      {showColorBreakdown && report ? (
        <IntakeV6LayersColorBreakdown report={report} />
      ) : null}

      {report && confirmation ? (
        <p className={v6.helper}>
          Confirmă rolul pentru fiecare strat, apoi folosește „Continuă la Review” din footer.
        </p>
      ) : null}
    </aside>
  );
}
