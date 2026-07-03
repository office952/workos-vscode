import { applyLayerRoleSelection, type LayerRoleConfirmation, type SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { resolveConfirmAllSuggestedRole } from "./intakeV6ArtworkOnlyGuard";
import type { IntakeV4LayerRoleSetup } from "./intakeV4Api";

function mapConfirmationStatus(
  status: LayerRoleConfirmation["confirmationStatus"],
): IntakeV4LayerRoleSetup["confirmation_status"] {
  if (status === "complete") return "complete";
  if (status === "partial") return "partial";
  return "missing";
}

export function layerRoleConfirmationToV4Setup(
  confirmation: LayerRoleConfirmation,
): IntakeV4LayerRoleSetup {
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
