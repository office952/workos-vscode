import type { OfferScopeMode, SoldModuleCode } from "./intakeV6OfferScopeState";
import { normalizeSoldModules } from "./intakeV6OfferScopeState";

export type OfferScopePresetId =
  | "full_product"
  | "face_only"
  | "cant_only"
  | "face_cant";

export type OfferScopePreset = {
  id: OfferScopePresetId;
  labelRo: string;
  mode: OfferScopeMode;
  soldModules: SoldModuleCode[];
  testId: string;
};

export const OFFER_SCOPE_PRESETS: OfferScopePreset[] = [
  {
    id: "full_product",
    labelRo: "Produs complet",
    mode: "full_product",
    soldModules: [],
    testId: "intake-v6-offer-scope-preset-full",
  },
  {
    id: "face_only",
    labelRo: "Doar față",
    mode: "component_subset",
    soldModules: ["FACE"],
    testId: "intake-v6-offer-scope-preset-face",
  },
  {
    id: "cant_only",
    labelRo: "Doar cant",
    mode: "component_subset",
    soldModules: ["RETURN-CANT"],
    testId: "intake-v6-offer-scope-preset-cant",
  },
  {
    id: "face_cant",
    labelRo: "Față + cant",
    mode: "component_subset",
    soldModules: ["FACE", "RETURN-CANT"],
    testId: "intake-v6-offer-scope-preset-face-cant",
  },
];

const MODULE_LABELS_RO: Record<SoldModuleCode, string> = {
  FACE: "Față",
  "RETURN-CANT": "Cant",
  BACK: "Spate",
  LIGHTING: "Iluminare",
  ELECTRICAL: "Electrică",
};

const PRIMARY_EXCLUSION_ORDER: SoldModuleCode[] = [
  "FACE",
  "RETURN-CANT",
  "BACK",
  "LIGHTING",
  "ELECTRICAL",
];

export function resolveActiveOfferScopePreset(
  mode: OfferScopeMode,
  soldModules: readonly SoldModuleCode[],
): OfferScopePresetId | null {
  if (mode === "full_product") {
    return "full_product";
  }
  const normalized = normalizeSoldModules([...soldModules]);
  const key = normalized.join(",");
  if (key === "FACE") return "face_only";
  if (key === "RETURN-CANT") return "cant_only";
  if (key === "FACE,RETURN-CANT" || key === "RETURN-CANT,FACE") return "face_cant";
  return null;
}

export function describeOfferScopeSummary(
  mode: OfferScopeMode,
  soldModules: readonly SoldModuleCode[],
): {
  requestModeLabelRo: string;
  activeLabelsRo: string[];
  excludedLabelsRo: string[];
} {
  if (mode === "full_product") {
    return {
      requestModeLabelRo: "Produs complet",
      activeLabelsRo: PRIMARY_EXCLUSION_ORDER.map((code) => MODULE_LABELS_RO[code]),
      excludedLabelsRo: [],
    };
  }
  const sold = new Set(normalizeSoldModules([...soldModules]));
  const activeLabelsRo = PRIMARY_EXCLUSION_ORDER.filter((code) => sold.has(code)).map(
    (code) => MODULE_LABELS_RO[code],
  );
  const excludedLabelsRo = PRIMARY_EXCLUSION_ORDER.filter((code) => !sold.has(code)).map(
    (code) => MODULE_LABELS_RO[code],
  );
  return {
    requestModeLabelRo: "Subset componente",
    activeLabelsRo,
    excludedLabelsRo,
  };
}
