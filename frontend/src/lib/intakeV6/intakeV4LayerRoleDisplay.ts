import type { LayerAutoRole, LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { INTAKE_V4_LAYER_ROLE_OPTIONS } from "./intakeV4LayerRoleOptions";

export interface IntakeV4LayerRoleDisplayRow {
  layerKey: string;
  layerName: string;
  kindLabel: string;
  layerKind?: "real" | "pseudo" | "raster_artwork";
  autoRole: LayerAutoRole;
  autoRoleLabel: string;
  selectedRole: LayerAutoRole;
  selectedRoleLabel: string;
  confirmationState: "pending" | "confirmed" | "ignored";
  paintKind: string;
  hint?: string | null;
}

function roleLabel(role: LayerAutoRole): string {
  return INTAKE_V4_LAYER_ROLE_OPTIONS.find((option) => option.value === role)?.label ?? role;
}

function kindLabelForLayer(layer: SvgAnalysisCoreReport["layers"][number]): string {
  if (layer.layerKind === "real") return "Corel layer";
  if (layer.layerKind === "pseudo") return "Pseudo-layer";
  if (layer.layerKind === "raster_artwork") return "Raster artwork";
  return "—";
}

function hintForLayer(layer: SvgAnalysisCoreReport["layers"][number]): string | null {
  if (layer.layerKind === "pseudo") return "Pseudo-layer generat din forme solide";
  if (layer.layerKind === "raster_artwork") return "Artwork raster — confirmă print";
  return null;
}

export function buildLayerRoleRowsForDisplay(
  report: SvgAnalysisCoreReport,
  confirmation: LayerRoleConfirmation | null,
): IntakeV4LayerRoleDisplayRow[] {
  return report.layers.map((layer) => {
    const entry =
      confirmation?.layers.find(
        (item) => item.layerKey === layer.id || item.layerKey === layer.name,
      ) ??
      confirmation?.layers.find((item) => item.layerName === layer.name);
    const layerKey = entry?.layerKey ?? layer.id ?? layer.name;
    const selectedRole = entry?.confirmedRole ?? layer.autoRole;
    return {
      layerKey,
      layerName: layer.name,
      kindLabel: kindLabelForLayer(layer),
      layerKind: layer.layerKind,
      autoRole: layer.autoRole,
      autoRoleLabel: roleLabel(layer.autoRole),
      selectedRole,
      selectedRoleLabel: roleLabel(selectedRole),
      confirmationState: entry?.confirmationState ?? "pending",
      paintKind: layer.paintEvidence.paintKind,
      hint: hintForLayer(layer),
    };
  });
}

export function countProductionGeometryLayers(report: SvgAnalysisCoreReport): number {
  return report.layers.filter((layer) => layer.autoRole === "face").length;
}

export function countArtworkLayers(report: SvgAnalysisCoreReport): number {
  return report.layers.filter((layer) =>
    layer.autoRole === "printed_artwork" || layer.autoRole === "logo",
  ).length;
}
