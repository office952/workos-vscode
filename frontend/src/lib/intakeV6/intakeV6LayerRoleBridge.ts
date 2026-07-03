import { applyLayerRoleSelection, type LayerRoleConfirmation, type SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { resolveConfirmAllSuggestedRole } from "./intakeV6ArtworkOnlyGuard";

export interface IntakeV6LayerRoleLayer {
  layer_key: string;
  layer_id?: string | null;
  layer_name?: string | null;
  auto_role: string;
  auto_confidence: string;
  confirmed_role?: string | null;
  confirmation_state: "pending" | "confirmed" | "ignored";
  operator_note?: string | null;
  path_count?: number | null;
  dominant_fill?: string | null;
}

export interface IntakeV6LayerRoleSetup {
  confirmation_status: "missing" | "partial" | "complete";
  layers: IntakeV6LayerRoleLayer[];
  warnings: string[];
}

function mapConfirmationStatus(
  status: LayerRoleConfirmation["confirmationStatus"],
): IntakeV6LayerRoleSetup["confirmation_status"] {
  if (status === "complete") return "complete";
  if (status === "partial") return "partial";
  return "missing";
}

export function layerRoleConfirmationToV6Setup(
  confirmation: LayerRoleConfirmation,
): IntakeV6LayerRoleSetup {
  return {
    confirmation_status: mapConfirmationStatus(confirmation.confirmationStatus),
    layers: confirmation.layers.map((layer) => ({
      layer_key: layer.layerKey,
      layer_id: layer.layerId,
      layer_name: layer.layerName,
      auto_role: layer.autoRole,
      auto_confidence: layer.autoConfidence,
      confirmed_role: layer.confirmedRole,
      confirmation_state: layer.confirmationState,
      operator_note: layer.operatorNote,
    })),
    warnings: [],
  };
}

export function confirmAllSuggestedLayerRoles(
  confirmation: LayerRoleConfirmation,
  report?: SvgAnalysisCoreReport | null,
): LayerRoleConfirmation {
  let next = confirmation;
  for (const layer of confirmation.layers) {
    if (layer.confirmationState !== "pending") continue;
    const reportLayer = report?.layers.find(
      (item) => item.id === layer.layerKey || item.name === layer.layerName || item.name === layer.layerKey,
    );
    const role = resolveConfirmAllSuggestedRole(layer, reportLayer);
    if (role == null) continue;
    next = applyLayerRoleSelection(next, layer.layerKey, role);
  }
  return next;
}

export function layerChipsFromLayerRoleConfirmation(
  confirmation: LayerRoleConfirmation | null,
): Array<{ layerKey: string; displayName: string; status: "pending" | "confirmed" | "ignored" }> {
  if (!confirmation) return [];
  return confirmation.layers.map((layer) => ({
    layerKey: layer.layerKey,
    displayName: layer.layerName ?? layer.layerId ?? layer.layerKey,
    status: layer.confirmationState,
  }));
}
