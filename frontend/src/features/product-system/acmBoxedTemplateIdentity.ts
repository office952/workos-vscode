/**
 * Canonical Product System identity for live ACM casetat template.
 * Display label owner-facing; code stays BOXED.
 */

export const ACM_BOXED_MOUNTING_TEMPLATE_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";

/**
 * Owner-facing product name (UI only — template code stays BOXED).
 * Shop aliases Dibond / ACM / ACP = same material family, not alternate product names.
 */
export const ACM_BOXED_OWNER_LABEL_RO = "Alucobond casetat";

/** Catalog family / category — not the product title. */
export const ACM_BOXED_FAMILY_LABEL_RO = "Panouri ACP / ACM";

export const ACM_BOXED_MATERIAL_PANEL_CODE = "MAT-ACM-BOND-PANEL";
/** Material alias strip — not the Product Template title. */
export const ACM_BOXED_MATERIAL_PANEL_LABEL_RO = "Panou ACM / Dibond / Alucobond";

export const ACM_BOXED_MATERIAL_FASTENERS_CODE = "MAT-SURUBURI-GEN";
export const ACM_BOXED_MATERIAL_FASTENERS_LABEL_RO = "Șuruburi / prinderi înecate";

export function isAcmBoxedMountingTemplate(
  templateCode: string | null | undefined,
): boolean {
  return (
    (templateCode ?? "").trim().toUpperCase() === ACM_BOXED_MOUNTING_TEMPLATE_CODE.toUpperCase()
  );
}

export const ACM_BOXED_COMPONENT_FACE_ID = "comp_acm_panel_face";
export const ACM_BOXED_COMPONENT_RETURNS_ID = "comp_casetted_returns";
export const ACM_BOXED_COMPONENT_FASTENERS_ID = "comp_mounting_fasteners";

export type AcmBoxedStructureComponentRef = {
  type: string;
  component_id: string;
  name: string;
};

function normalizeId(value: string): string {
  return value.trim().toLowerCase();
}

export function isAcmBoxedFaceStructureComponent(
  component: AcmBoxedStructureComponentRef,
): boolean {
  return normalizeId(component.component_id) === ACM_BOXED_COMPONENT_FACE_ID;
}

export function isAcmBoxedCasetareStructureComponent(
  component: AcmBoxedStructureComponentRef,
): boolean {
  return normalizeId(component.component_id) === ACM_BOXED_COMPONENT_RETURNS_ID;
}

export function isAcmBoxedAssemblyStructureComponent(
  component: AcmBoxedStructureComponentRef,
): boolean {
  return normalizeId(component.component_id) === ACM_BOXED_COMPONENT_FASTENERS_ID;
}
