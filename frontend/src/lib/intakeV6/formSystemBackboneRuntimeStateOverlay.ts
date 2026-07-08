import type { IntakeV6LayerRoleLayer, IntakeV6LayerRoleSetup } from "./intakeV6LayerRoleBridge";
import type { FormSystemBackboneFieldProjection } from "./formSystemBackboneFieldProjection";

export interface FormSystemRuntimeStateOverlayInput {
  layerRoleSetup?: IntakeV6LayerRoleSetup | null;
}

const OVERLAYABLE_FIELD_KEYS = new Set(["svg.layer_group_role", "svg.selected_layer_group"]);
const EXCLUDED_FIELD_KEYS = new Set([
  "lighting.psu_configuration",
  "material.led_psu",
  "materials.led_psu",
]);
const GENERIC_UNCONFIRMED_WARNINGS = new Set([
  "Suggested value only; operator confirmation is still required.",
  "Field is missing and does not represent confirmed truth.",
]);

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function cloneProjection(entry: FormSystemBackboneFieldProjection): FormSystemBackboneFieldProjection {
  return {
    ...entry,
    warnings: [...entry.warnings],
    blockers: [...entry.blockers],
    trace: { ...entry.trace },
  };
}

function confirmedLayers(layerRoleSetup: IntakeV6LayerRoleSetup | null | undefined): IntakeV6LayerRoleLayer[] {
  if (!layerRoleSetup || !Array.isArray(layerRoleSetup.layers)) return [];
  return layerRoleSetup.layers.filter((layer) => {
    return layer.confirmation_state === "confirmed" && text(layer.confirmed_role) != null;
  });
}

function selectedLayerRefs(layers: IntakeV6LayerRoleLayer[]): { ids: string[]; names: string[]; roles: string[] } {
  const ids = [...new Set(layers.map((layer) => text(layer.layer_id) ?? text(layer.layer_key)).filter((value): value is string => Boolean(value)))];
  const names = [...new Set(layers.map((layer) => text(layer.layer_name)).filter((value): value is string => Boolean(value)))];
  const roles = [...new Set(layers.map((layer) => text(layer.confirmed_role)).filter((value): value is string => Boolean(value)))];
  return { ids, names, roles };
}

function canOverlayConfirmedLayerState(layerRoleSetup: IntakeV6LayerRoleSetup | null | undefined): boolean {
  if (!layerRoleSetup || layerRoleSetup.confirmation_status !== "complete") return false;
  return confirmedLayers(layerRoleSetup).length > 0;
}

function applyConfirmedOverlay(
  projection: FormSystemBackboneFieldProjection,
  layerRoleSetup: IntakeV6LayerRoleSetup,
): FormSystemBackboneFieldProjection {
  const confirmed = confirmedLayers(layerRoleSetup);
  const refs = selectedLayerRefs(confirmed);
  return {
    ...projection,
    sourceKind: "operator_manual",
    state: "confirmed",
    isConfirmedTruth: true,
    isDerived: false,
    isBlocking: false,
    warnings: projection.warnings.filter((warning) => !GENERIC_UNCONFIRMED_WARNINGS.has(warning)),
    blockers: [],
    trace: {
      ...projection.trace,
      sourceType: "operator_confirmed",
      rawState: "confirmed",
      overlayApplied: true,
      overlayOriginalState: projection.state,
      overlayOriginalSourceKind: projection.sourceKind,
      overlayRuntimeConfirmationStatus: layerRoleSetup.confirmation_status,
      overlayRuntimeConfirmedLayerCount: confirmed.length,
      overlaySelectedLayerIds: refs.ids,
      overlaySelectedLayerNames: refs.names,
      overlayConfirmedRoles: refs.roles,
    },
  };
}

export function applyFormSystemRuntimeStateOverlay(
  projection: FormSystemBackboneFieldProjection[],
  runtimeState: FormSystemRuntimeStateOverlayInput,
): FormSystemBackboneFieldProjection[] {
  const layerRoleSetup = runtimeState.layerRoleSetup ?? null;
  const canOverlayConfirmed = canOverlayConfirmedLayerState(layerRoleSetup);

  return projection.map((entry) => {
    const next = cloneProjection(entry);
    if (EXCLUDED_FIELD_KEYS.has(next.fieldKey)) return next;
    if (!OVERLAYABLE_FIELD_KEYS.has(next.fieldKey)) return next;
    if (!canOverlayConfirmed || !layerRoleSetup) return next;
    return applyConfirmedOverlay(next, layerRoleSetup);
  });
}