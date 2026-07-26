/**
 * Near-top action map for Work Intake detail — visibility/routing only.
 */
import {
  ArrowRight,
  CheckCircle2,
  XCircle,
  MapPin,
  Layers,
  FileText,
  AlertTriangle,
} from "lucide-react";
import {
  INTAKE_SECTION_IDS,
  type IntakeActionSummaryModel,
  type IntakeSectionAnchor,
} from "@/lib/intakeActionSummary";

interface IntakeActionSummaryProps {
  model: IntakeActionSummaryModel;
  onPrimaryAction: () => void;
  onOpenPreliminaryQuote?: () => void;
  showProductForm: boolean;
  requiresInstallAudit: boolean;
}

function StatusCell({
  label,
  value,
  ok,
}: {
  label: string;
  value: string;
  ok: boolean | null;
}) {
  const icon =
    ok === null ? (
      <span className="w-3.5 h-3.5 rounded-full bg-slate-600 shrink-0" />
    ) : ok ? (
      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
    ) : (
      <XCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
    );

  return (
    <div className="min-w-0">
      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
        {label}
      </p>
      <p className="text-[12px] text-slate-200 flex items-center gap-1.5 truncate">
        {icon}
        <span className="truncate font-medium">{value}</span>
      </p>
    </div>
  );
}

function JumpLink({
  label,
  anchor,
  icon,
}: {
  label: string;
  anchor: IntakeSectionAnchor;
  icon: React.ReactNode;
}) {
  const href = `#${INTAKE_SECTION_IDS[anchor]}`;
  return (
    <a
      href={href}
      className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-semibold text-blue-300 bg-blue-950/30 border border-blue-900/40 hover:bg-blue-900/40 hover:text-blue-200 transition-colors"
    >
      {icon}
      {label}
    </a>
  );
}

export default function IntakeActionSummary({
  model,
  onPrimaryAction,
  onOpenPreliminaryQuote,
  showProductForm,
  requiresInstallAudit,
}: IntakeActionSummaryProps) {
  const primaryIsQuote =
    model.primaryAction === "open_preliminary_quote" &&
    model.showPreliminaryQuote;

  return (
    <div
      id="intake-action-summary"
      data-testid="intake-action-summary"
      className="bg-wo-surface-raised border border-blue-900/40 rounded-lg p-4 ring-1 ring-blue-900/20"
    >
      <div className="flex items-center gap-2 mb-3">
        <FileText className="w-4 h-4 text-blue-400 shrink-0" />
        <h2 className="text-[13px] font-semibold text-slate-100">
          Hartă acțiuni — unde ești și ce urmează
        </h2>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <StatusCell
          label="Template"
          value={model.templateLabel}
          ok={model.templateOk}
        />
        <StatusCell
          label="Specificație produs"
          value={model.productSpecLabel}
          ok={model.productSpecOk}
        />
        <StatusCell
          label="Teren"
          value={model.terrainLabel}
          ok={model.terrainOk}
        />
        <StatusCell
          label="Status intake"
          value={model.intakeStatusLabel}
          ok={model.intakeReady}
        />
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">
            Următoarea acțiune
          </p>
          <div className="flex flex-col gap-1">
            <button
              type="button"
              onClick={() => {
                if (primaryIsQuote && onOpenPreliminaryQuote) {
                  onOpenPreliminaryQuote();
                } else {
                  onPrimaryAction();
                }
              }}
              disabled={model.primaryDisabled || model.primaryAction === "none"}
              className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-[12px] font-bold transition-colors w-fit ${
                model.primaryDisabled || model.primaryAction === "none"
                  ? "bg-slate-700/60 text-slate-500 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-500 text-white"
              }`}
            >
              {model.primaryActionLabel}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            {model.primaryDisabled && model.primaryDisabledReason && (
              <p className="text-[10px] text-amber-400/90 max-w-md">
                {model.primaryDisabledReason}
              </p>
            )}
          </div>
        </div>

        {model.showPreliminaryQuote && model.intakeReady && onOpenPreliminaryQuote && (
          <button
            type="button"
            onClick={onOpenPreliminaryQuote}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[11px] font-semibold bg-emerald-900/30 text-emerald-300 border border-emerald-800/50 hover:bg-emerald-900/50 transition-colors w-fit"
          >
            Deschide ofertare preliminară
            <ArrowRight className="w-3 h-3" />
          </button>
        )}
      </div>

      {model.stagedMissingGroups.some(
        (g) => g.stage !== "stage0_unresolved" && g.missing.length > 0
      ) && (
        <div
          className="mb-3 px-3 py-2 bg-amber-950/25 border border-amber-900/30 rounded-lg space-y-2"
          data-testid="staged-readiness-summary"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <p className="text-[11px] text-amber-300 font-medium">
              Condiții pe etape — {model.readinessStageLabel}
            </p>
          </div>
          {model.stagedMissingGroups
            .filter(
              (g) => g.stage !== "stage0_unresolved" && g.missing.length > 0
            )
            .map((group) => (
              <div key={group.stage} data-testid={`summary-stage-${group.stage}`}>
                <p className="text-[10px] text-slate-400 font-medium mb-0.5">
                  {group.label}:
                </p>
                <ul className="text-[10px] text-amber-300/80 list-disc pl-5 space-y-0.5">
                  {group.missing.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </div>
            ))}
          {model.canSimulate &&
            !model.intakeReady &&
            model.stagedMissingGroups.some(
              (g) =>
                g.stage === "stage3_commercial_quote" && g.missing.length > 0
            ) && (
              <p className="text-[10px] text-blue-300/90">
                Simulare disponibilă. Oferta comercială finală mai are condiții.
              </p>
            )}
        </div>
      )}

      <div className="flex flex-wrap gap-2 pt-2 border-t border-wo-border-subtle">
        <span className="text-[10px] text-slate-500 self-center mr-1">
          Salt rapid:
        </span>
        {!model.templateOk && (
          <JumpLink
            label="Confirmă template"
            anchor="template"
            icon={<Layers className="w-3 h-3" />}
          />
        )}
        {showProductForm && (
          <JumpLink
            label="Mergi la specificație produs"
            anchor="product-spec"
            icon={<FileText className="w-3 h-3" />}
          />
        )}
        {showProductForm && (
          <JumpLink
            label="Mergi la materiale client"
            anchor="product-spec"
            icon={<Layers className="w-3 h-3" />}
          />
        )}
        {requiresInstallAudit && (
          <JumpLink
            label="Mergi la teren"
            anchor="terrain"
            icon={<MapPin className="w-3 h-3" />}
          />
        )}
        {model.showPreliminaryQuote && onOpenPreliminaryQuote && (
          <button
            type="button"
            onClick={onOpenPreliminaryQuote}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-semibold text-purple-300 bg-purple-950/30 border border-purple-900/40 hover:bg-purple-900/40 transition-colors"
          >
            Deschide ofertare preliminară
            <ArrowRight className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
}
