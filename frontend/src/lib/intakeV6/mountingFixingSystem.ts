/** Technical wall fixing system — independent of commercial mounting_scope. */

export const VERTICAL_STEEL_BRACKET = "FIXING-SYSTEM-VERTICAL-STEEL-BRACKET";
export const PROFILE_SHS_20X20X1_5 = "PROFILE-SHS-20X20X1_5";
export const MAT_STRUCT_STEEL = "MAT-STRUCT-STEEL";

export type MountingFixingSystem = {
  type_code: string | null;
  material_code: string | null;
  main_profile_code: string | null;
  top_angle: {
    resource_type: string;
    dimension_status: string;
    length_mm: number | null;
    notes?: string;
  } | null;
  bottom_horizontal_bar: {
    material_code: string;
    dimension_status: string;
    length_mm: number | null;
    notes?: string;
  } | null;
  lower_fastener: {
    type: string;
    owner_label: string;
    diameter_mm: number;
    length_mm: number;
  } | null;
  confirmation_status: string;
  quantity_status: string;
  blockers?: string[];
  provenance?: Record<string, unknown>;
};

export function emptyMountingFixingSystem(): MountingFixingSystem {
  return {
    type_code: null,
    material_code: null,
    main_profile_code: null,
    top_angle: null,
    bottom_horizontal_bar: null,
    lower_fastener: null,
    confirmation_status: "NOT_APPLICABLE",
    quantity_status: "NOT_APPLICABLE",
    blockers: [],
    provenance: { contract_version: "mounting_fixing_system/v1" },
  };
}

export function selectVerticalSteelBracket(): MountingFixingSystem {
  return {
    type_code: VERTICAL_STEEL_BRACKET,
    material_code: MAT_STRUCT_STEEL,
    main_profile_code: PROFILE_SHS_20X20X1_5,
    top_angle: {
      resource_type: "STEEL_ANGLE",
      dimension_status: "MANUAL_CONFIRMATION_REQUIRED",
      length_mm: null,
      notes: "Cornier debitat la lucrare — fără cotă fixă.",
    },
    bottom_horizontal_bar: {
      material_code: MAT_STRUCT_STEEL,
      dimension_status: "MANUAL_CONFIRMATION_REQUIRED",
      length_mm: null,
      notes: "Bara orizontală debitată la lucrare — fără cotă fixă.",
    },
    lower_fastener: {
      type: "SELF_DRILLING_HEX_HEAD",
      owner_label: "Autoforante cap hexagonal 4.5x60 mm",
      diameter_mm: 4.5,
      length_mm: 60,
    },
    confirmation_status: "CONFIRMED_WITH_MANUAL_DIMENSIONS",
    quantity_status: "CONFIGURED_WITH_MANUAL_DIMENSIONS",
    blockers: [],
    provenance: {
      source: "INTAKE_STEP_2",
      contract_version: "mounting_fixing_system/v1",
    },
  };
}

export function readMountingFixingSystem(
  finish: Record<string, unknown> | null | undefined,
): MountingFixingSystem {
  const raw = finish?.mounting_fixing_system;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return emptyMountingFixingSystem();
  }
  const typed = raw as MountingFixingSystem;
  if (!typed.type_code) return emptyMountingFixingSystem();
  return typed;
}
