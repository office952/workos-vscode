import { displayModuleTemplateWireLabel } from "./productTemplateModulesVocabulary";

export interface ReturnCantReadonlyContainerFieldAudit {
  key:
    | "instance_id"
    | "component_template_code"
    | "component_id"
    | "layer_group_ids"
    | "source_face_component_id"
    | "source_face_perimeter_ref"
    | "perimeter_source"
    | "confirmed_perimeter_m"
    | "material_profile"
    | "depth_mm"
    | "finish_type"
    | "color_source"
    | "operation_modelare_cant_ref"
    | "operation_bonding_ref"
    | "resource_requirements_ref"
    | "confirmation_state"
    | "blockers";
  label: string;
  sourceType:
    | "component truth"
    | "component dependency anchor"
    | "Form System capture"
    | "root geometry context"
    | "parent aggregate support"
    | "legacy alias"
    | "component template / registry"
    | "missing";
  currentSource: string;
  targetPath: string;
  note: string;
}

export interface ReturnCantReadonlyContainerModel {
  componentKey: "return_cant";
  targetContainerPath: "components.return_cant.instances[]";
  legacyAliasPaths: string[];
  upstreamDependencies: Array<{
    key: string;
    canonicalPath: string;
    status: "blocked" | "partial";
    note: string;
  }>;
  sourceTypeRows: ReturnCantReadonlyContainerFieldAudit[];
  blockers: string[];
  readiness: "blocked" | "partial";
  productAggregateBoundaryNote: string;
  missingTruthFields: string[];
}

const SOURCE_TYPE_ROWS: ReturnCantReadonlyContainerFieldAudit[] = [
  {
    key: "instance_id",
    label: "instance_id",
    sourceType: "missing",
    currentSource: "not stabilized; readonly rows still keyed by group/artwork source rows",
    targetPath: "components.return_cant.instances[].instance_id",
    note: "Container target is canonical, but stable instance ids are not yet first-class runtime truth.",
  },
  {
    key: "component_template_code",
    label: displayModuleTemplateWireLabel("component_template_code"),
    sourceType: "component template / registry",
    currentSource: "TPL-VOLUM-ALUMINIU_v1",
    targetPath: "components.return_cant.instances[].component_template_code",
    note: "The structural boundary is already real at the Module produs (child Product Template) level.",
  },
  {
    key: "component_id",
    label: "component_id",
    sourceType: "component template / registry",
    currentSource: "comp_lateral_litere",
    targetPath: "components.return_cant.instances[].component_id",
    note: "The structural component id is stable in seed, dossier, and ProductAggregate mapping.",
  },
  {
    key: "layer_group_ids",
    label: "layer_group_ids",
    sourceType: "missing",
    currentSource: "selected_layer_refs and layer confirmations exist, but are not mapped as component truth",
    targetPath: "components.return_cant.instances[].layer_group_ids",
    note: "Still blocked until layer-group selection is component-scoped.",
  },
  {
    key: "source_face_component_id",
    label: "source_face_component_id",
    sourceType: "parent aggregate support",
    currentSource: "implied by comp_face_litere in composition/read-model",
    targetPath: "components.return_cant.instances[].source_face_component_id",
    note: "The dependency owner exists conceptually, but is not yet written as explicit instance truth.",
  },
  {
    key: "source_face_perimeter_ref",
    label: "source_face_perimeter_ref",
    sourceType: "component dependency anchor",
    currentSource: "components.face.confirmed_perimeter",
    targetPath: "components.return_cant.instances[].source_face_perimeter_ref",
    note: "Canonical dependency anchor only. Actual resolved reference is not migrated yet, so readiness stays blocked.",
  },
  {
    key: "perimeter_source",
    label: "perimeter_source",
    sourceType: "root geometry context",
    currentSource: "quote_geometry.letter_perimeter_m",
    targetPath: "components.return_cant.instances[].perimeter_source",
    note: "Current root geometry evidence is context only; dependency remains blocked until face-confirmed perimeter is explicit.",
  },
  {
    key: "confirmed_perimeter_m",
    label: "confirmed_perimeter_m",
    sourceType: "missing",
    currentSource: "letter_perimeter_m exists, but not as component-owned confirmed_perimeter_m for return_cant",
    targetPath: "components.return_cant.instances[].confirmed_perimeter_m",
    note: "This must come from the face dependency, not from aggregate hydration.",
  },
  {
    key: "material_profile",
    label: "material_profile",
    sourceType: "component template / registry",
    currentSource: "profile width/material gates in TPL-VOLUM-ALUMINIU_v1",
    targetPath: "components.return_cant.instances[].material_profile",
    note: "The material family exists on the Module produs (child Product Template), but the selected truth field is still missing.",
  },
  {
    key: "depth_mm",
    label: "depth_mm",
    sourceType: "Form System capture",
    currentSource: "finish_setup.return_depth_mm",
    targetPath: "components.return_cant.instances[].depth_mm",
    note: "Current depth is still capture/hydration, not confirmed component truth.",
  },
  {
    key: "finish_type",
    label: "finish_type",
    sourceType: "Form System capture",
    currentSource: "finish_setup.return_finish_type",
    targetPath: "components.return_cant.instances[].finish_type",
    note: "Current finish token is still capture/hydration, not a completed component-owned field.",
  },
  {
    key: "color_source",
    label: "color_source",
    sourceType: "Form System capture",
    currentSource: "return_oracal_code / finish_setup + reusable finish interpretation",
    targetPath: "components.return_cant.instances[].color_source",
    note: "Color remains coupled to finish capture and catalog interpretation.",
  },
  {
    key: "operation_modelare_cant_ref",
    label: "operation_modelare_cant_ref",
    sourceType: "component template / registry",
    currentSource: "RETURN_PROFILE_MACHINE_FORMING / modelare_cant",
    targetPath: "components.return_cant.instances[].operation_modelare_cant_ref",
    note: "Operation exists already; truth inputs are what remain incomplete.",
  },
  {
    key: "operation_bonding_ref",
    label: "operation_bonding_ref",
    sourceType: "component template / registry",
    currentSource: "RETURN_PROFILE_FACE_BONDING",
    targetPath: "components.return_cant.instances[].operation_bonding_ref",
    note: "Bonding reference exists as operation identity, not yet as instance-bound truth.",
  },
  {
    key: "resource_requirements_ref",
    label: "resource_requirements_ref",
    sourceType: "parent aggregate support",
    currentSource: "operation_resource_requirements remains external operational registry boundary",
    targetPath: "components.return_cant.instances[].resource_requirements_ref",
    note: "Read-only only; do not treat workcenter hints as component truth.",
  },
  {
    key: "confirmation_state",
    label: "confirmation_state",
    sourceType: "missing",
    currentSource: "workflow/global confirmations only",
    targetPath: "components.return_cant.instances[].confirmation_state",
    note: "No row/global confirmation can be treated as final component confirmation.",
  },
  {
    key: "blockers",
    label: "blockers",
    sourceType: "component truth",
    currentSource: "readonly mapper blockers",
    targetPath: "components.return_cant.instances[].blockers[]",
    note: "Blockers are already explicit and should stay visible until source paths are real.",
  },
];

export function buildReturnCantReadonlyContainerModel(): ReturnCantReadonlyContainerModel {
  return {
    componentKey: "return_cant",
    targetContainerPath: "components.return_cant.instances[]",
    legacyAliasPaths: ["components.returnCant.depthMm", "components.returnCant.finishType", "components.returnCant.colorCode"],
    upstreamDependencies: [
      {
        key: "face_confirmed_perimeter",
        canonicalPath: "components.face.confirmed_perimeter",
        status: "blocked",
        note: "Return/cant depends on FACE confirmed perimeter and must not invent its own perimeter from root context.",
      },
    ],
    sourceTypeRows: SOURCE_TYPE_ROWS,
    blockers: [
      "RETURN_CANT_MATERIAL_MISSING",
      "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
      "RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED",
    ],
    readiness: "blocked",
    productAggregateBoundaryNote:
      "ProductAggregate is derived read model, not truth source. Parent aggregate or root geometry support rows may explain runtime behavior, but they do not satisfy component-owned truth requirements.",
    missingTruthFields: [
      "instance_id",
      "layer_group_ids",
      "source_face_perimeter_ref",
      "confirmed_perimeter_m",
      "material_profile",
      "confirmation_state",
    ],
  };
}