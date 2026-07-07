import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { applyLayerRoleSelection } from "@/lib/svgAnalyzer";
import {
  ARTWORK_ONLY_REVIEW_TITLE,
  ARTWORK_ONLY_STEP1_MESSAGE,
  artworkOnlyDecisionPending,
  artworkOnlyLayerDisplayType,
  detectArtworkOnlyRequiresDecision,
  layerIsArtworkCandidate,
} from "@/lib/intakeV6/intakeV6ArtworkOnlyGuard";
import { INTAKE_V6_LOGO_TEMPLATE_CODE } from "@/lib/intakeV6/intakeV6LayerTargetTemplate";
import { buildOperatorLogoLabelMap, getOperatorLayerLabel } from "@/lib/intakeV6/intakeV4OperatorUiDisplay";
import { AlertTriangle, ImageIcon, Upload } from "lucide-react";
import { v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6ArtworkOnlyDecisionPanel({
  report,
  confirmation,
  onUpdateLayerRole,
  onRequestReload,
  variant = "step1",
}: {
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  onUpdateLayerRole?: (layerKey: string, role: "printed_artwork" | "ignore") => void;
  onRequestReload?: () => void;
  variant?: "step1" | "review";
}) {
  if (!detectArtworkOnlyRequiresDecision(report, confirmation)) return null;
  if (!artworkOnlyDecisionPending(report, confirmation)) return null;

  const candidateLayers = report.layers.filter((layer) => layerIsArtworkCandidate(layer));
  const sourceFileName = (report.sourceFileName ?? "").trim().toLowerCase();
  const logoLabelMap = buildOperatorLogoLabelMap(report.layers);

  return (
    <div
      className={`${v6.cardCompact} border-amber-500/35 bg-amber-500/10`}
      data-testid={`intake-v6-artwork-only-decision-${variant}`}
    >
      <div className="mb-3 flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" aria-hidden />
        <div>
          <h3 className="text-[12px] font-semibold text-amber-100">
            {variant === "review" ? ARTWORK_ONLY_REVIEW_TITLE : "Logo / vector constructiv — confirmare necesară"}
          </h3>
          <p className="mt-1 text-[11px] leading-relaxed text-amber-100/90">{ARTWORK_ONLY_STEP1_MESSAGE}</p>
          <p className="mt-1 text-[11px] leading-relaxed text-amber-100/90" data-testid={`intake-v6-logo-template-candidate-${variant}`}>
            Template recomandabil: {INTAKE_V6_LOGO_TEMPLATE_CODE} · confirmarea compoziției decide Product Truth.
          </p>
        </div>
      </div>

      <ul className="space-y-2" data-testid="intake-v6-artwork-only-layer-list">
        {candidateLayers.map((layer) => {
          const entry =
            confirmation.layers.find((item) => item.layerKey === layer.id || item.layerKey === layer.name) ??
            confirmation.layers.find((item) => item.layerName === layer.name);
          const normalizedName = (layer.name ?? "").trim().toLowerCase().replace(/-/g, " ");
          const normalizedId = (layer.id ?? "").trim().toLowerCase().replace(/-/g, " ");
          const displayName = sourceFileName === "logo.svg" && (normalizedName === "logo stanga" || normalizedName === "logo dreapta" || normalizedId === "logo stanga" || normalizedId === "logo dreapta")
            ? "Logo volumetric"
            : getOperatorLayerLabel(layer.id, layer.name, { logoLabelMap });
          const roleLabel = entry?.confirmationState === "pending" ? "needs decision" : entry?.confirmedRole ?? entry?.autoRole;
          const confidence = entry?.autoConfidence ?? "low";

          return (
            <li
              key={layer.id}
              className="rounded border border-amber-500/25 bg-[#0B1220]/60 p-3"
              data-testid={`intake-v6-artwork-only-layer-${layer.id}`}
            >
              <div className="flex items-start gap-2">
                <ImageIcon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-300/80" aria-hidden />
                <div className="min-w-0 flex-1">
                  <p className="text-[11px] font-semibold text-slate-100">{displayName}</p>
                  <p className="mt-0.5 text-[10px] text-slate-400">
                    type: {artworkOnlyLayerDisplayType(layer)} · role: {roleLabel} · confidence: {confidence}
                  </p>
                  {onUpdateLayerRole ? (
                    <div className="mt-2 flex flex-wrap gap-2">
                      <button
                        type="button"
                        className={`${v6.btnGhost} !px-2 !py-1 text-[10px]`}
                        data-testid={`intake-v6-artwork-only-confirm-${layer.id}`}
                        onClick={() => onUpdateLayerRole(entry?.layerKey ?? layer.id, "printed_artwork")}
                      >
                        Confirmă ca logo/vector
                      </button>
                      <button
                        type="button"
                        className={`${v6.btnGhost} !px-2 !py-1 text-[10px]`}
                        data-testid={`intake-v6-artwork-only-exclude-${layer.id}`}
                        onClick={() => onUpdateLayerRole(entry?.layerKey ?? layer.id, "ignore")}
                      >
                        Ignoră stratul
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      {onRequestReload ? (
        <button
          type="button"
          className={`${v6.btnGhost} mt-3 inline-flex w-full items-center justify-center gap-1.5 text-[11px]`}
          data-testid="intake-v6-artwork-only-reload"
          onClick={onRequestReload}
        >
          <Upload className="h-3.5 w-3.5" aria-hidden />
          Reîncarcă SVG cu alte straturi
        </button>
      ) : null}
    </div>
  );
}

export function applyArtworkOnlyLayerDecision(
  confirmation: LayerRoleConfirmation,
  layerKey: string,
  decision: "printed_artwork" | "ignore",
): LayerRoleConfirmation {
  if (decision === "ignore") {
    return applyLayerRoleSelection(confirmation, layerKey, "ignore");
  }
  return applyLayerRoleSelection(confirmation, layerKey, "printed_artwork");
}
