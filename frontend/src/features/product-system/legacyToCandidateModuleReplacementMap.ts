export type LegacyReplacementReadiness =
  | "mapped"
  | "partial_mapping"
  | "needs_owner_decision"
  | "blocked_until_component_truth"
  | "keep_for_history";

export type LegacyReplacementRisk = "low" | "medium" | "high";

export type LegacyReplacementMapEntry = {
  legacyCode: string;
  legacyLabel: string;
  legacyType:
    | "legacy_internal_module"
    | "legacy_shared_module"
    | "legacy_product_root_dependency"
    | "legacy_logo_dependency"
    | "legacy_mounting_dependency";

  usedBy: string[];
  currentUse:
    | "used_by_active_letters_root"
    | "used_by_logo_candidate"
    | "shared_contract"
    | "historical_or_unknown";

  replacementTargetCode: string | null;
  replacementTargetLabel: string | null;
  replacementTargetType:
    | "component_template"
    | "product_composer"
    | "no_direct_replacement"
    | "owner_decision_required";

  migrationTruthAreas: string[];
  missingTruthAreas: string[];
  deprecationReadiness: LegacyReplacementReadiness;
  risk: LegacyReplacementRisk;

  canDeleteNow: false;
  deleteBlockers: string[];

  ownerNoteRo: string;
};

export type LegacyReplacementOverallVerdict =
  | "not_ready_for_delete"
  | "mapping_started"
  | "ready_for_deprecation_plan"
  | "ready_for_delete";

export type LegacyReplacementSummary = {
  totalLegacyEntries: number;
  mappedCount: number;
  partialCount: number;
  ownerDecisionCount: number;
  blockedCount: number;
  deletableNowCount: number;
  usedByActiveRootCount: number;
  highRiskCount: number;
  overallVerdict: LegacyReplacementOverallVerdict;
};

const SHARED_DELETE_BLOCKERS = [
  "Component truth not confirmed",
  "ProductDefinition not consuming component truth",
  "Pricing not migrated",
  "Old orders/snapshots may reference legacy",
  "Work Intake active root still uses legacy composition",
] as const;

export const LEGACY_TO_CANDIDATE_MODULE_REPLACEMENT_MAP: LegacyReplacementMapEntry[] = [
  {
    legacyCode: "TPL-VOLUMETRIC-FACE_v1",
    legacyLabel: "Volumetric face module",
    legacyType: "legacy_shared_module",
    usedBy: ["TPL-VOLUMETRIC-LETTERS_v2", "TPL-VOLUMETRIC-LOGO_v1"],
    currentUse: "used_by_active_letters_root",
    replacementTargetCode: "TPL-COMP-LETTER-FACE_v1",
    replacementTargetLabel: "Module produs — Față",
    replacementTargetType: "component_template",
    migrationTruthAreas: [
      "material față",
      "grosime față",
      "suprafață / cut path / bounding",
      "finisaj față legat de face",
    ],
    missingTruthAreas: ["component-owned face truth confirmed", "ProductDefinition face consumption"],
    deprecationReadiness: "blocked_until_component_truth",
    risk: "high",
    canDeleteNow: false,
    deleteBlockers: [...SHARED_DELETE_BLOCKERS],
    ownerNoteRo:
      "Nu șterge acum. Modulul legacy de față este încă legat de produsul activ și de contractele partajate cu LOGO.",
  },
  {
    legacyCode: "TPL-VOLUMETRIC-BACK_v1",
    legacyLabel: "Volumetric back module",
    legacyType: "legacy_shared_module",
    usedBy: ["TPL-VOLUMETRIC-LETTERS_v2"],
    currentUse: "used_by_active_letters_root",
    replacementTargetCode: "TPL-COMP-LETTER-BACK_v1",
    replacementTargetLabel: "Module produs — Spate",
    replacementTargetType: "component_template",
    migrationTruthAreas: [
      "material spate",
      "grosime spate",
      "prindere spate",
      "distanțe / găuri / backing logic",
    ],
    missingTruthAreas: ["back geometry ref from face", "backing mode confirmed"],
    deprecationReadiness: "blocked_until_component_truth",
    risk: "high",
    canDeleteNow: false,
    deleteBlockers: [...SHARED_DELETE_BLOCKERS],
    ownerNoteRo:
      "Nu șterge acum. Spatele legacy este încă folosit de compoziția activă TPL-VOLUMETRIC-LETTERS_v2.",
  },
  {
    legacyCode: "TPL-VOLUMETRIC-LED_v1",
    legacyLabel: "Volumetric lighting / LED module",
    legacyType: "legacy_shared_module",
    usedBy: ["TPL-VOLUMETRIC-LETTERS_v2", "TPL-VOLUMETRIC-LOGO_v1"],
    currentUse: "used_by_active_letters_root",
    replacementTargetCode: "TPL-COMP-LETTER-LED_v1",
    replacementTargetLabel: "Module produs — Iluminare",
    replacementTargetType: "component_template",
    migrationTruthAreas: [
      "tip LED",
      "densitate LED",
      "putere",
      "sursă",
      "wiring",
      "calc LED",
    ],
    missingTruthAreas: ["LED truth not component-owned confirmed", "pricing LED not migrated"],
    deprecationReadiness: "blocked_until_component_truth",
    risk: "high",
    canDeleteNow: false,
    deleteBlockers: [...SHARED_DELETE_BLOCKERS, "Runtime not activated for component LED"],
    ownerNoteRo:
      "Nu șterge acum. Strategia LED legacy este încă folosită de root-ul activ și candidatul LOGO.",
  },
  {
    legacyCode: "TPL-VOLUM-ALUMINIU_v1",
    legacyLabel: "Volum aluminiu / return-cant module",
    legacyType: "legacy_shared_module",
    usedBy: ["TPL-VOLUMETRIC-LETTERS_v2", "TPL-VOLUMETRIC-LOGO_v1"],
    currentUse: "used_by_active_letters_root",
    replacementTargetCode: "TPL-COMP-LETTER-RETURN-CANT_v1",
    replacementTargetLabel: "Module produs — Cant / volum",
    replacementTargetType: "component_template",
    migrationTruthAreas: [
      "cant stock",
      "Oracal",
      "Vopsit RAL",
      "lățime / volum cant",
      "material cant",
      "manoperă cant",
      "rules calcul separat",
    ],
    missingTruthAreas: [
      "return/cant final Product Truth not confirmed",
      "RAL material + manoperă not wired",
      "perimeter source not confirmed",
    ],
    deprecationReadiness: "partial_mapping",
    risk: "high",
    canDeleteNow: false,
    deleteBlockers: [...SHARED_DELETE_BLOCKERS, "Return/cant overlap with legacy aliases"],
    ownerNoteRo:
      "Nu șterge acum. Cantul legacy are dependențe de perimetru față și truth parțial confirmat.",
  },
  {
    legacyCode: "TPL-VOLUMETRIC-FINISH_v1",
    legacyLabel: "Volumetric finish / artwork module",
    legacyType: "legacy_shared_module",
    usedBy: ["TPL-VOLUMETRIC-LETTERS_v2"],
    currentUse: "used_by_active_letters_root",
    replacementTargetCode: "TPL-COMP-LETTER-FINISH_v1",
    replacementTargetLabel: "Module produs — Finisaj",
    replacementTargetType: "component_template",
    migrationTruthAreas: ["folie", "print", "laminare", "vopsire", "finisaj vizual"],
    missingTruthAreas: ["overlap cu FACE/RETURN-CANT trebuie clarificat", "operator fields not finalized"],
    deprecationReadiness: "partial_mapping",
    risk: "medium",
    canDeleteNow: false,
    deleteBlockers: [...SHARED_DELETE_BLOCKERS, "Finish target overlap with face/return"],
    ownerNoteRo:
      "Nu șterge acum. Finisajul legacy se suprapune parțial cu față și cant — necesită decizie owner.",
  },
  {
    legacyCode: "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    legacyLabel: "Metal premount / mounting structure",
    legacyType: "legacy_mounting_dependency",
    usedBy: ["TPL-VOLUMETRIC-LETTERS_v2"],
    currentUse: "used_by_active_letters_root",
    replacementTargetCode: "TPL-COMP-LETTER-MOUNTING_v1",
    replacementTargetLabel: "Module produs — Montaj",
    replacementTargetType: "component_template",
    migrationTruthAreas: [
      "montaj",
      "șablon",
      "distanțieri",
      "structură suport",
      "dibluri / șuruburi",
      "premount",
    ],
    missingTruthAreas: ["mounting truth not confirmed", "execution/mounting not migrated"],
    deprecationReadiness: "blocked_until_component_truth",
    risk: "medium",
    canDeleteNow: false,
    deleteBlockers: [...SHARED_DELETE_BLOCKERS, "Execution/mounting handoff not migrated"],
    ownerNoteRo:
      "Nu șterge acum. Interfața de montaj legacy este încă folosită de produsul activ.",
  },
  {
    legacyCode: "TPL-VOLUMETRIC-LETTERS_v1",
    legacyLabel: "Legacy volumetric letters root (v1)",
    legacyType: "legacy_product_root_dependency",
    usedBy: [],
    currentUse: "historical_or_unknown",
    replacementTargetCode: "TPL-LETTERS-COMPOSER_v1",
    replacementTargetLabel: "Product Template (candidate only)",
    replacementTargetType: "product_composer",
    migrationTruthAreas: ["product orchestration only — not material truth"],
    missingTruthAreas: ["full candidate-module truth stack", "runtime activation", "Work Intake cutover"],
    deprecationReadiness: "keep_for_history",
    risk: "high",
    canDeleteNow: false,
    deleteBlockers: [...SHARED_DELETE_BLOCKERS, "Historical snapshots may reference v1 root"],
    ownerNoteRo:
      "Nu șterge acum. Root legacy istoric — păstrat pentru referință, nu pentru activare.",
  },
];

export function normalizeLegacyTemplateCode(code: string | null | undefined): string {
  return String(code ?? "").trim().toUpperCase();
}

export function getLegacyReplacementEntry(legacyCode: string): LegacyReplacementMapEntry | null {
  const normalized = normalizeLegacyTemplateCode(legacyCode);
  return (
    LEGACY_TO_CANDIDATE_MODULE_REPLACEMENT_MAP.find(
      (entry) => normalizeLegacyTemplateCode(entry.legacyCode) === normalized,
    ) ?? null
  );
}

export function resolveLegacyReplacementEntry(legacyCode: string): LegacyReplacementMapEntry {
  const known = getLegacyReplacementEntry(legacyCode);
  if (known) return known;

  const normalized = normalizeLegacyTemplateCode(legacyCode);
  const isLegacyPattern =
    /^(TPL-VOLUMETRIC-|TPL-VOLUM-|TPL-METAL-)/.test(normalized) &&
    !normalized.startsWith("TPL-COMP-LETTER-");

  return {
    legacyCode,
    legacyLabel: "Legacy module (unmapped)",
    legacyType: "legacy_internal_module",
    usedBy: [],
    currentUse: "historical_or_unknown",
    replacementTargetCode: null,
    replacementTargetLabel: null,
    replacementTargetType: isLegacyPattern ? "owner_decision_required" : "no_direct_replacement",
    migrationTruthAreas: [],
    missingTruthAreas: ["mapping not defined in contract"],
    deprecationReadiness: "needs_owner_decision",
    risk: "medium",
    canDeleteNow: false,
    deleteBlockers: [...SHARED_DELETE_BLOCKERS, "No approved replacement mapping"],
    ownerNoteRo:
      "Nu șterge acum. Modulul legacy nu are încă mapping aprobat către candidate-module.",
  };
}

export function buildLegacyReplacementSummary(
  entries: LegacyReplacementMapEntry[] = LEGACY_TO_CANDIDATE_MODULE_REPLACEMENT_MAP,
): LegacyReplacementSummary {
  const mappedCount = entries.filter((e) => e.deprecationReadiness === "mapped").length;
  const partialCount = entries.filter((e) => e.deprecationReadiness === "partial_mapping").length;
  const ownerDecisionCount = entries.filter((e) => e.deprecationReadiness === "needs_owner_decision").length;
  const blockedCount = entries.filter((e) => e.deprecationReadiness === "blocked_until_component_truth").length;
  const usedByActiveRootCount = entries.filter((e) => e.currentUse === "used_by_active_letters_root").length;
  const highRiskCount = entries.filter((e) => e.risk === "high").length;
  const deletableNowCount = entries.filter((e) => e.canDeleteNow === true).length;

  return {
    totalLegacyEntries: entries.length,
    mappedCount,
    partialCount,
    ownerDecisionCount,
    blockedCount,
    deletableNowCount,
    usedByActiveRootCount,
    highRiskCount,
    overallVerdict: computeLegacyReplacementOverallVerdict(entries, deletableNowCount),
  };
}

export function computeLegacyReplacementOverallVerdict(
  entries: LegacyReplacementMapEntry[] = LEGACY_TO_CANDIDATE_MODULE_REPLACEMENT_MAP,
  deletableNowCount = entries.filter((e) => e.canDeleteNow === true).length,
): LegacyReplacementOverallVerdict {
  if (deletableNowCount > 0) {
    return "ready_for_delete";
  }

  const hasBlocked = entries.some(
    (e) =>
      e.deprecationReadiness === "blocked_until_component_truth" ||
      e.currentUse === "used_by_active_letters_root",
  );

  if (hasBlocked) {
    return "not_ready_for_delete";
  }

  const mappedRatio =
    entries.length === 0
      ? 0
      : entries.filter((e) => e.replacementTargetCode != null).length / entries.length;

  if (mappedRatio >= 0.9) {
    return "ready_for_deprecation_plan";
  }

  if (mappedRatio > 0) {
    return "mapping_started";
  }

  return "not_ready_for_delete";
}

export function legacyReplacementStatusLabel(readiness: LegacyReplacementReadiness): string {
  switch (readiness) {
    case "mapped":
      return "MAPPED";
    case "partial_mapping":
      return "PARTIAL";
    case "needs_owner_decision":
      return "OWNER DECISION";
    case "blocked_until_component_truth":
      return "BLOCKED";
    case "keep_for_history":
      return "KEEP FOR HISTORY";
    default:
      return "BLOCKED";
  }
}

export const CANDIDATE_MODULE_REPLACEMENT_CONTEXT = [
  {
    componentCode: "TPL-COMP-LETTER-FACE_v1",
    label: "FACE",
    replacesLegacy: ["TPL-VOLUMETRIC-FACE_v1"],
    summaryRo: "FACE înlocuiește modulul legacy de față.",
  },
  {
    componentCode: "TPL-COMP-LETTER-BACK_v1",
    label: "BACK",
    replacesLegacy: ["TPL-VOLUMETRIC-BACK_v1"],
    summaryRo: "BACK înlocuiește modulul legacy de spate.",
  },
  {
    componentCode: "TPL-COMP-LETTER-RETURN-CANT_v1",
    label: "RETURN/CANT",
    replacesLegacy: ["TPL-VOLUM-ALUMINIU_v1"],
    summaryRo: "RETURN-CANT înlocuiește modulul legacy cant/aluminiu.",
  },
  {
    componentCode: "TPL-COMP-LETTER-LED_v1",
    label: "LED",
    replacesLegacy: ["TPL-VOLUMETRIC-LED_v1"],
    summaryRo: "LED înlocuiește modulul legacy de iluminat.",
  },
  {
    componentCode: "TPL-COMP-LETTER-FINISH_v1",
    label: "FINISH",
    replacesLegacy: ["TPL-VOLUMETRIC-FINISH_v1"],
    summaryRo: "FINISH înlocuiește modulul legacy de finisaj.",
  },
  {
    componentCode: "TPL-COMP-LETTER-MOUNTING_v1",
    label: "MOUNTING",
    replacesLegacy: ["TPL-METAL-PREMOUNT-STRUCTURE_v1"],
    summaryRo: "MOUNTING înlocuiește modulul legacy de premount/montaj.",
  },
] as const;
