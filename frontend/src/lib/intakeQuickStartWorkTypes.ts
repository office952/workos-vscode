import type { ProductFamily } from "@/api/productFamilies";
import { LITERE_VOLUMETRICE_FAMILY_ID } from "@/lib/intakeProductSpec";
import { UNRESOLVED_INTAKE_PRODUCT_FAMILY } from "@/lib/intakeProductFamilyDisplay";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

export type IntakeQuickStartWorkType = {
  id: string;
  label: string;
  hint?: string;
  /** Registry family_id; null on generic work type (stored as empty product_family). */
  familyId: string | null;
  templateCode?: string;
  enabled: boolean;
  disabledReason?: string;
};

/** Curated operator-facing work types — human labels only in UI. */
export const INTAKE_QUICK_START_WORK_TYPES: IntakeQuickStartWorkType[] = [
  {
    id: "volumetric",
    label: "Litere volumetrice",
    familyId: LITERE_VOLUMETRICE_FAMILY_ID,
    templateCode: TPL_VOLUMETRIC_LETTERS,
    enabled: true,
  },
  {
    id: "lightbox",
    label: "Casete luminoase",
    familyId: "casete_luminoase",
    enabled: false,
    disabledReason: "În curând",
  },
  {
    id: "print",
    label: "Print / banner",
    familyId: "print_large_format",
    enabled: true,
  },
  {
    id: "sticker",
    label: "Autocolant / sticker",
    familyId: "vinyl_stickers",
    enabled: false,
    disabledReason: "În curând",
  },
  {
    id: "signage",
    label: "Semnalistică",
    familyId: "semnalistica_interioara",
    enabled: false,
    disabledReason: "În curând",
  },
  {
    id: "totem",
    label: "Totem / pylon",
    familyId: "semnalistica_exterioara",
    enabled: false,
    disabledReason: "În curând",
  },
  {
    id: "generic",
    label: "Nu știu încă / Cerere generică",
    familyId: null,
    hint: "Creează o cerere draft și alegi tipul lucrării mai târziu.",
    enabled: true,
  },
];

export function isGenericQuickStartWorkType(workTypeId: string | null | undefined): boolean {
  return workTypeId === "generic";
}

export function isWorkTypeSelectable(
  workType: IntakeQuickStartWorkType,
  registry: ProductFamily[]
): boolean {
  const families = registry ?? [];
  if (!workType.enabled) return false;
  if (workType.id === "generic") {
    return families.some((family) => family.active);
  }
  if (!workType.familyId) return false;
  return families.some((family) => family.active && family.family_id === workType.familyId);
}

/**
 * Resolves create payload product_family.
 * Returns null when selection is invalid; empty string for generic/unresolved.
 */
export function resolveWorkTypeFamilyId(
  workTypeId: string | null,
  registry: ProductFamily[]
): string | null {
  if (!workTypeId) return null;
  const workType = INTAKE_QUICK_START_WORK_TYPES.find((item) => item.id === workTypeId);
  if (!workType || !isWorkTypeSelectable(workType, registry)) return null;
  if (workType.id === "generic") return UNRESOLVED_INTAKE_PRODUCT_FAMILY;
  return workType.familyId;
}

export type QuickStartMissingField = "work_type" | "description" | "channel" | "registry";

const MISSING_LABELS: Record<QuickStartMissingField, string> = {
  work_type: "tip lucrare",
  description: "descriere",
  channel: "canal",
  registry: "registry familii",
};

export function getQuickStartMissingRequirements(input: {
  workTypeId: string | null;
  description: string;
  channel: string;
  registry: ProductFamily[];
  registryLoading: boolean;
  registryError: string | null;
}): QuickStartMissingField[] {
  const missing: QuickStartMissingField[] = [];
  if (input.registryLoading || input.registryError) {
    missing.push("registry");
    return missing;
  }
  if (!input.workTypeId) {
    missing.push("work_type");
  } else {
    const workType = INTAKE_QUICK_START_WORK_TYPES.find((item) => item.id === input.workTypeId);
    if (!workType || !isWorkTypeSelectable(workType, input.registry)) {
      missing.push("work_type");
    }
  }
  if (!input.description.trim()) {
    missing.push("description");
  }
  if (!input.channel.trim()) {
    missing.push("channel");
  }
  return missing;
}

export function formatMissingRequirementsMessage(missing: QuickStartMissingField[]): string | null {
  if (missing.length === 0) return null;
  if (missing.includes("registry")) {
    return "Registry-ul de familii nu este disponibil. Reîncearcă după ce backend-ul răspunde.";
  }
  const labels = missing.map((field) => MISSING_LABELS[field]);
  return `Completează: ${labels.join(", ")}.`;
}
