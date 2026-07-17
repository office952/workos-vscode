import type {
  IntakeV6ModularFormContractResponse,
  IntakeV6ModularFormFieldBinding,
} from "./intakeV6ModularFormContractTypes";

export const LETTERS_CANONICAL_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2";

export const LETTERS_CANONICAL_TEMPLATE_ALIASES = ["TPL-VOLUMETRIC-LETTERS"] as const;

export type LettersCanonicalBindMap = ReadonlyMap<string, IntakeV6ModularFormFieldBinding>;

export interface LettersCanonicalFieldLabels {
  face_finish_type: string;
  return_finish_type: string;
  return_depth_mm: string;
  backing_mode: string;
  lighting_system_type: string;
  mounting_system: string;
}

const DEFAULT_FIELD_LABELS: LettersCanonicalFieldLabels = {
  face_finish_type: "Finisaj față",
  return_finish_type: "Finisaj cant / volum",
  return_depth_mm: "Adâncime cant / volum (mm)",
  backing_mode: "Finisaj spate",
  lighting_system_type: "Sistem LED",
  mounting_system: "Sistem montaj",
};

export function isLettersCanonicalTemplate(templateCode: string | null | undefined): boolean {
  const normalized = templateCode?.trim();
  if (!normalized) return false;
  if (normalized === LETTERS_CANONICAL_TEMPLATE_CODE) return true;
  return LETTERS_CANONICAL_TEMPLATE_ALIASES.includes(
    normalized as (typeof LETTERS_CANONICAL_TEMPLATE_ALIASES)[number],
  );
}

export function bindMapFromContract(
  contract: IntakeV6ModularFormContractResponse | null | undefined,
): LettersCanonicalBindMap {
  const map = new Map<string, IntakeV6ModularFormFieldBinding>();
  for (const binding of contract?.field_bindings ?? []) {
    const key = binding.canonical_key?.trim();
    if (key) {
      map.set(key, binding);
    }
  }
  return map;
}

export function labelForKey(
  bindMap: LettersCanonicalBindMap,
  canonicalKey: string,
  fallback: string,
): string {
  const label = bindMap.get(canonicalKey)?.label_ro?.trim();
  return label || fallback;
}

export function requiredForKey(
  bindMap: LettersCanonicalBindMap,
  canonicalKey: string,
  fallback = false,
): boolean {
  const binding = bindMap.get(canonicalKey);
  return binding?.required ?? fallback;
}

export function resolveLettersCanonicalFieldLabels(
  templateCode: string | null | undefined,
  contract: IntakeV6ModularFormContractResponse | null | undefined,
): LettersCanonicalFieldLabels | null {
  if (!isLettersCanonicalTemplate(templateCode) || !contract) {
    return null;
  }
  const bindMap = bindMapFromContract(contract);
  return {
    face_finish_type: labelForKey(bindMap, "face_finish_type", DEFAULT_FIELD_LABELS.face_finish_type),
    return_finish_type: labelForKey(
      bindMap,
      "return_finish_type",
      DEFAULT_FIELD_LABELS.return_finish_type,
    ),
    return_depth_mm: labelForKey(bindMap, "return_depth_mm", DEFAULT_FIELD_LABELS.return_depth_mm),
    backing_mode: labelForKey(bindMap, "backing_mode", DEFAULT_FIELD_LABELS.backing_mode),
    lighting_system_type: labelForKey(
      bindMap,
      "lighting_system_type",
      DEFAULT_FIELD_LABELS.lighting_system_type,
    ),
    mounting_system: labelForKey(bindMap, "mounting_system", DEFAULT_FIELD_LABELS.mounting_system),
  };
}
