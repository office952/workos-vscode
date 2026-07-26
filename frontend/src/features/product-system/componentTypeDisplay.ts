/**
 * Display-only labels for ProductSystem component types.
 * Internal `type` enums and template JSON are unchanged.
 */

import type { ProductComponentType, ProductTemplateComponent } from "@/lib/api";
import {
  ACM_BOXED_CORP_STRUCTURE_TYPE_LABEL,
  ACM_BOXED_FRAME_STRUCTURE_TYPE_LABEL,
} from "./acmBoxedStructureDocumentation";
import {
  isAcmBoxedAssemblyStructureComponent,
  isAcmBoxedCasetareStructureComponent,
  isAcmBoxedFaceStructureComponent,
  isAcmBoxedMountingTemplate,
} from "./acmBoxedTemplateIdentity";

export const VOLUMETRIC_LETTERS_TEMPLATE_CODES = new Set([
  "TPL-VOLUMETRIC-LETTERS",
  "TPL-VOLUMETRIC-LETTERS_V2",
]);

export function isVolumetricLettersTemplate(
  templateCode: string | null | undefined,
): boolean {
  return VOLUMETRIC_LETTERS_TEMPLATE_CODES.has((templateCode ?? "").trim().toUpperCase());
}

function normalizeForMatch(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
}

/**
 * Volumetric-letter display category (null → use COMPONENT_TYPE_CONFIG.label).
 */
export function getVolumetricLettersComponentTypeDisplayLabel(
  component: Pick<ProductTemplateComponent, "type" | "component_id" | "name">,
): string | null {
  const id = normalizeForMatch(component.component_id);
  const name = normalizeForMatch(component.name);

  if (component.type === "STRUCTURA") {
    if (
      id.includes("premont") ||
      id.includes("suport") ||
      id.includes("cadru") ||
      name.includes("premont") ||
      name.includes("suport") ||
      name.includes("structura metalica") ||
      name.includes("cadru metalic")
    ) {
      return "Structură metalică";
    }
    if (id.includes("spate") || name.includes("spate") || name.includes("forex")) {
      return "Capac spate";
    }
    return "Volum / Profil";
  }

  if (component.type === "LITERE_3D") {
    if (
      id.includes("lateral") ||
      id.includes("bordur") ||
      id.includes("profil") ||
      name.includes("lateral") ||
      name.includes("bordur") ||
      name.includes("profil") ||
      name.includes("aluminiu")
    ) {
      return "Volum aluminiu";
    }
    if (id.includes("face") || id.includes("fata") || name.includes("fata")) {
      return "Vizual față";
    }
    return "Volum / Profil";
  }

  return null;
}

/**
 * Seed BOM comps under ACM all belong to Corp casetat teaching card —
 * never label face as "Structură metalică" (that name is reserved for the frame).
 */
export function getAcmBoxedComponentTypeDisplayLabel(
  component: Pick<ProductTemplateComponent, "type" | "component_id" | "name">,
): string | null {
  if (
    isAcmBoxedFaceStructureComponent(component) ||
    isAcmBoxedCasetareStructureComponent(component) ||
    isAcmBoxedAssemblyStructureComponent(component)
  ) {
    return ACM_BOXED_CORP_STRUCTURE_TYPE_LABEL;
  }
  const id = normalizeForMatch(component.component_id);
  const name = normalizeForMatch(component.name);
  if (id.includes("frame") || id.includes("cadru") || name.includes("cadru") || name.includes("frame")) {
    return ACM_BOXED_FRAME_STRUCTURE_TYPE_LABEL;
  }
  return null;
}

export function getComponentTypeDisplayLabel(
  component: Pick<ProductTemplateComponent, "type" | "component_id" | "name">,
  templateCode: string | null | undefined,
  defaultLabel: string,
): string {
  if (isAcmBoxedMountingTemplate(templateCode)) {
    return getAcmBoxedComponentTypeDisplayLabel(component) ?? defaultLabel;
  }
  if (!isVolumetricLettersTemplate(templateCode)) {
    return defaultLabel;
  }
  return getVolumetricLettersComponentTypeDisplayLabel(component) ?? defaultLabel;
}

/** Short label for type select options on volumetric templates (enum value unchanged). */
export function getComponentTypeSelectOptionLabel(
  type: ProductComponentType,
  templateCode: string | null | undefined,
  defaultLabel: string,
): string {
  if (!isVolumetricLettersTemplate(templateCode)) {
    return defaultLabel;
  }
  if (type === "STRUCTURA") {
    return "Capac spate (tip STRUCTURA)";
  }
  if (type === "LITERE_3D") {
    return "Volum / Profil (tip LITERE_3D)";
  }
  return defaultLabel;
}
