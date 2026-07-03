import type { ProductTruthDraftBuilderInput } from "./productTruthTypes";

const baseLayers = [
  { layer_key: "pseudo:maria", layer_name: "maria", auto_role: "face" },
  { layer_key: "pseudo:soare", layer_name: "soare", auto_role: "face" },
  { layer_key: "pseudo:ana", layer_name: "ana", auto_role: "face" },
  { layer_key: "pseudo:gradinita", layer_name: "gradinita", auto_role: "face" },
  { layer_key: "logo-stanga", layer_name: "logo stanga", auto_role: "printed_artwork" },
  { layer_key: "logo-dreapta", layer_name: "logo dreapta", auto_role: "printed_artwork" },
] as const;

function pendingLayers() {
  return baseLayers.map((layer) => ({ ...layer, confirmation_state: "pending" as const }));
}

function confirmedLayers(overrides: Record<string, Partial<(typeof baseLayers)[number]> & { operator_decision?: "printed" | "artwork_only" | "ignored" | null }> = {}) {
  return baseLayers.map((layer) => ({
    ...layer,
    ...overrides[layer.layer_key],
    confirmed_role: overrides[layer.layer_key]?.auto_role ?? layer.auto_role,
    confirmation_state: "confirmed" as const,
  }));
}

const completeLetterGroupFinishes = [
  { group_key: "pseudo:maria", layer_name: "maria", face_finish_type: "oracal_651", face_oracal_code: "056", return_finish_type: "white_aluminum", return_depth_mm: 60, face_vinyl_roll_width_mm: 1000, confirmed: true },
  { group_key: "pseudo:soare", layer_name: "soare", face_finish_type: "oracal_651", face_oracal_code: "032", return_finish_type: "white_aluminum", return_depth_mm: 60, face_vinyl_roll_width_mm: 1000, confirmed: true },
  { group_key: "pseudo:ana", layer_name: "ana", face_finish_type: "oracal_651", face_oracal_code: "056", return_finish_type: "white_aluminum", return_depth_mm: 60, face_vinyl_roll_width_mm: 1000, confirmed: true },
  { group_key: "pseudo:gradinita", layer_name: "gradinita", face_finish_type: "oracal_651", face_oracal_code: "032", return_finish_type: "white_aluminum", return_depth_mm: 60, face_vinyl_roll_width_mm: 1000, confirmed: true },
];

const printedArtworkFinishes = [
  { layer_key: "logo-stanga", layer_name: "logo stanga", artwork_decision: "printed" as const, execution_type: "print_laminate", print_required: true, lamination_required: true, estimated_area_m2: 0.4002, material_code: "print_vinyl_laminated", confirmed: true },
  { layer_key: "logo-dreapta", layer_name: "logo dreapta", artwork_decision: "printed" as const, execution_type: "print_laminate", print_required: true, lamination_required: true, estimated_area_m2: 0.4003, material_code: "print_vinyl_laminated", confirmed: true },
];

const baseCompleteFixture: ProductTruthDraftBuilderInput = {
  workspaceId: "c8dda47f-e2a7-4fea-800c-2dc01b2be5a3",
  workspaceCode: "IV6-BB8EE3F8",
  intakeId: "IR-MR18L96M",
  templateCode: "TPL-VOLUMETRIC-LETTERS_v2",
  productFamily: "volumetric_letters",
  generatedAt: "2026-07-01T00:00:00.000Z",
  svgSource: {
    fileName: "gradi-curat.svg",
    sourceHash: "593c4d439157b83cab16c33d69caf0ab426144d583fb1999fa7d1676d5ab6cf1",
    analysisStatus: "parsed",
  },
  quoteGeometry: {
    width_mm: 5086.99,
    height_mm: 600.03,
    letter_count: 19,
    face_area_m2: 1.2638,
    return_material_perimeter_ml: 29.9098,
    geometry_source: "nest2_face_parts_outer",
    confirmed: true,
  },
  layerRoleSetup: {
    confirmation_status: "complete",
    warnings: [],
    layers: confirmedLayers(),
  },
  finishSetup: {
    face_material_family: "plexiglas_opal",
    face_material_confirmed: true,
    face_thickness_mm: 3,
    face_thickness_confirmed: true,
    face_finish_type: "oracal_651",
    face_vinyl_roll_width_mm: 1000,
    finish_target: "face",
    return_finish_type: "white_aluminum",
    return_depth_mm: 60,
    illuminated: true,
    lighting_system_type: "led_modules",
    light_color: "neutral",
    led_module_power_w: 0.75,
    selected_psu_watts: 100,
    backing_mode: "forex_10_no_bevel",
    back_bevel_enabled: false,
    mounting_scope: "mounting_included",
    mounting_system: "direct_wall",
    mounting_template_enabled: true,
    mounting_template_area_m2: 3.052,
    mounting_template_material_type: "forex",
    support_required: "no",
    support_quote_relevant: false,
    letter_group_finishes: completeLetterGroupFinishes,
    artwork_finishes: printedArtworkFinishes,
    confirmed: true,
  },
};

function fixture(overrides: Partial<ProductTruthDraftBuilderInput>): ProductTruthDraftBuilderInput {
  return {
    ...baseCompleteFixture,
    ...overrides,
    svgSource: { ...baseCompleteFixture.svgSource, ...overrides.svgSource },
    quoteGeometry: { ...baseCompleteFixture.quoteGeometry, ...overrides.quoteGeometry },
    layerRoleSetup: { ...baseCompleteFixture.layerRoleSetup, ...overrides.layerRoleSetup },
    finishSetup: { ...baseCompleteFixture.finishSetup, ...overrides.finishSetup },
  };
}

export const gradiCuratUnconfirmedFixture: ProductTruthDraftBuilderInput = fixture({
  layerRoleSetup: {
    confirmation_status: "missing",
    warnings: ["PERIMETER_CONFIDENCE_MEDIUM"],
    layers: pendingLayers(),
  },
  finishSetup: {
    face_material_confirmed: false,
    face_thickness_confirmed: false,
    finish_target: null,
    mounting_scope: null,
    support_required: null,
    letter_group_finishes: completeLetterGroupFinishes.map((group) => ({ ...group, confirmed: false })),
    artwork_finishes: printedArtworkFinishes.map((artwork) => ({ ...artwork, artwork_decision: null, confirmed: false })),
    confirmed: false,
  },
});

export const gradiCuratConfirmedRolesFixture: ProductTruthDraftBuilderInput = fixture({
  finishSetup: {
    face_material_confirmed: false,
    face_thickness_confirmed: false,
    finish_target: null,
    mounting_scope: null,
    support_required: null,
    artwork_finishes: [],
  },
});

export const gradiCuratCompleteReviewLikeFixture: ProductTruthDraftBuilderInput = baseCompleteFixture;

export const gradiCuratSupportMountingMismatchFixture: ProductTruthDraftBuilderInput = fixture({
  finishSetup: {
    mounting_system: "steel_bars",
    support_required: null,
    support_type: null,
    support_source: null,
    support_quote_relevant: null,
  },
});

export const gradiCuratArtworkIgnoredFixture: ProductTruthDraftBuilderInput = fixture({
  layerRoleSetup: {
    confirmation_status: "complete",
    warnings: [],
    layers: confirmedLayers({
      "logo-stanga": { auto_role: "printed_artwork", operator_decision: "ignored" },
      "logo-dreapta": { auto_role: "printed_artwork", operator_decision: "ignored" },
    }),
  },
  finishSetup: {
    artwork_finishes: printedArtworkFinishes.map((artwork) => ({ ...artwork, artwork_decision: "ignored" as const, execution_type: "ignore", print_required: false, lamination_required: false, confirmed: true })),
  },
});

export const gradiCuratArtworkOnlyFixture: ProductTruthDraftBuilderInput = fixture({
  finishSetup: {
    artwork_finishes: printedArtworkFinishes.map((artwork) => ({ ...artwork, artwork_decision: "artwork_only" as const, execution_type: "vinyl_cut", print_required: false, lamination_required: false, confirmed: true })),
  },
});

export const gradiCuratPrintNoLaminateFixture: ProductTruthDraftBuilderInput = fixture({
  finishSetup: {
    artwork_finishes: printedArtworkFinishes.map((artwork) => ({ ...artwork, artwork_decision: "printed" as const, execution_type: "print", print_required: true, lamination_required: false, confirmed: true })),
  },
});

export const gradiCuratLaminateWithoutPrintWarningFixture: ProductTruthDraftBuilderInput = fixture({
  finishSetup: {
    artwork_finishes: printedArtworkFinishes.map((artwork) => ({ ...artwork, artwork_decision: "printed" as const, execution_type: "vinyl_cut", print_required: false, lamination_required: true, confirmed: true })),
  },
});

export const gradiCuratMissingFinishTargetFixture: ProductTruthDraftBuilderInput = fixture({
  finishSetup: {
    finish_target: null,
  },
});

export const gradiCuratExecutionOnlyElectricalFixture: ProductTruthDraftBuilderInput = fixture({
  finishSetup: {
    psu_placement: "inside_letter_group",
    extra_cable_or_site_details: "PSU placement and extra cable length to be decided on site.",
    extra_cable_quote_scope: false,
  },
});

export const gradiCuratUnconfirmedProductTruthInput = gradiCuratUnconfirmedFixture;
export const gradiCuratConfirmedWithBarMountingProductTruthInput = gradiCuratSupportMountingMismatchFixture;
