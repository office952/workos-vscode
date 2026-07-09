import {
  RETURN_CANT_OWNER_INPUTS,
  type OwnerConfirmedValueStatus,
} from "./componentFirstReturnCantOwnerInputs";

export const RETURN_CANT_OWNER_ANSWERS_DOC_PATH =
  "docs/worklog/owner-input/return_cant_owner_answers_pending.md";

export type OwnerAnswerDocStatus = "pending" | "answered" | "partial" | "blocked";

export type ReturnCantOwnerAnswerTopic = {
  priority: number;
  section: string;
  topic: string;
  questionRo: string;
  contractKeys: string[];
  docStatus: OwnerAnswerDocStatus;
  notesRo: string;
};

/**
 * Workshop-only mirror of owner-answers doc state.
 * Updated d64c427 → apply v2: owner answers from prompt applied to contract.
 */
export const RETURN_CANT_OWNER_ANSWER_TOPICS: ReturnCantOwnerAnswerTopic[] = [
  {
    priority: 1,
    section: "A",
    topic: "Oracal selector",
    questionRo: "Selector coduri uzuale + alt cod? Listă completă? Text liber?",
    contractKeys: ["oracal_selector_mode"],
    docStatus: "answered",
    notesRo: "Mod listă completă confirmat — catalog efectiv (oracal_code_list) încă pending.",
  },
  {
    priority: 2,
    section: "A",
    topic: "Oracal pricing",
    questionRo: "Preț unic sau preț pe cod/familie?",
    contractKeys: ["oracal_pricing_mode"],
    docStatus: "answered",
    notesRo: "Mod preț pe cod/familie confirmat — tabel prețuri încă pending.",
  },
  {
    priority: 3,
    section: "B",
    topic: "RAL mode",
    questionRo: "Text liber? Selector standard? Selector + text liber?",
    contractKeys: ["ral_input_mode"],
    docStatus: "answered",
    notesRo: "Selector standard confirmat — sursă/listă RAL încă pending.",
  },
  {
    priority: 4,
    section: "C",
    topic: "Adâncimi cant",
    questionRo: "30 / 60 / 80 / 100 mm? altele?",
    contractKeys: ["return_depths_standard"],
    docStatus: "answered",
    notesRo: "30 / 60 / 80 / 100 mm confirmate.",
  },
  {
    priority: 5,
    section: "D",
    topic: "Material cant",
    questionRo: "Aluminiu? PVC? plexi? alt material?",
    contractKeys: ["return_material"],
    docStatus: "answered",
    notesRo: "Aluminiu 0.6 mm confirmat.",
  },
  {
    priority: 6,
    section: "D",
    topic: "Material vs adâncime",
    questionRo: "Același material 30/60 mm sau diferit?",
    contractKeys: ["return_material"],
    docStatus: "answered",
    notesRo: "Un singur material aluminiu 0.6 mm pentru toate adâncimile.",
  },
  {
    priority: 7,
    section: "E",
    topic: "Unitate material",
    questionRo: "ml / mp / buc / set? Perimetru cant ca bază?",
    contractKeys: ["return_material_unit"],
    docStatus: "answered",
    notesRo: "ml confirmat.",
  },
  {
    priority: 8,
    section: "E",
    topic: "Unitate manoperă",
    questionRo: "ml / mp / buc / set?",
    contractKeys: ["return_labor_unit"],
    docStatus: "answered",
    notesRo: "ml confirmat.",
  },
  {
    priority: 9,
    section: "F",
    topic: "RAL material price",
    questionRo: "Preț material 30/60/80 mm? Unitate?",
    contractKeys: ["ral_material_price_rule"],
    docStatus: "partial",
    notesRo: "Unitate ml confirmată — prețuri lipsă.",
  },
  {
    priority: 10,
    section: "G",
    topic: "RAL manoperă + minim",
    questionRo: "ml / set / piesă / minim + ml? Există minim?",
    contractKeys: ["ral_labor_price_rule", "minimum_price_rule"],
    docStatus: "answered",
    notesRo:
      "Manoperă 1.00 EUR/ml confirmată. Minim 100 lei pe culoare RAL, aplicat la total material + manoperă.",
  },
  {
    priority: 11,
    section: "H",
    topic: "Culoare Stock pricing",
    questionRo: "Influențează prețul sau doar info atelier?",
    contractKeys: ["stock_color_affects_price"],
    docStatus: "answered",
    notesRo: "NU — doar informație atelier.",
  },
  {
    priority: 12,
    section: "I",
    topic: "Perimetru / geometrie",
    questionRo: "Perimetru litere? bounding/nesting/contur? Product Truth path?",
    contractKeys: ["perimeter_geometry_source"],
    docStatus: "answered",
    notesRo: "Perimetru/contur real al literelor confirmat.",
  },
  {
    priority: 13,
    section: "I",
    topic: "Compatibilitate material ↔ adâncime",
    questionRo: "Ce combinații sunt valide?",
    contractKeys: ["material_depth_compatibility"],
    docStatus: "pending",
    notesRo: "Blocant ProductDefinition — neconfirmat.",
  },
];

export type ReturnCantOwnerApplyPlan = {
  answersFound: boolean;
  answersSource: typeof RETURN_CANT_OWNER_ANSWERS_DOC_PATH | "owner_prompt" | "none";
  topicsPending: number;
  topicsAnswered: number;
  topicsPartial: number;
  contractKeysReadyToApply: string[];
  contractKeysStillPending: string[];
  applyBlockedReason: string;
  nextSliceTitle: string;
  globalWorkshopStatus: "OWNER_INPUT_REQUIRED";
};

export function buildReturnCantOwnerApplyPlan(
  topics: ReturnCantOwnerAnswerTopic[] = RETURN_CANT_OWNER_ANSWER_TOPICS,
): ReturnCantOwnerApplyPlan {
  const answeredTopics = topics.filter((t) => t.docStatus === "answered");
  const partialTopics = topics.filter((t) => t.docStatus === "partial");
  const answersFound = answeredTopics.length > 0 || partialTopics.length > 0;

  const contractKeysReadyToApply = answeredTopics.flatMap((t) => t.contractKeys);
  const uniqueReady = [...new Set(contractKeysReadyToApply)];

  const allPendingKeys = RETURN_CANT_OWNER_INPUTS.filter(
    (i) => i.status === "owner_input_required",
  ).map((i) => i.key);

  const contractKeysStillPending = allPendingKeys.filter((k) => !uniqueReady.includes(k));

  return {
    answersFound,
    answersSource: answersFound ? "owner_prompt" : "none",
    topicsPending: topics.filter((t) => t.docStatus === "pending").length,
    topicsAnswered: answeredTopics.length,
    topicsPartial: partialTopics.length,
    contractKeysReadyToApply: uniqueReady,
    contractKeysStillPending,
    applyBlockedReason: answersFound
      ? "Partial catalog/pricing data still pending — no pricing activation"
      : "No owner answers — contract values unchanged",
    nextSliceTitle: "COMPONENT_FIRST_RETURN_CANT_CATALOG_AND_PRICING_DATA_V3",
    globalWorkshopStatus: "OWNER_INPUT_REQUIRED",
  };
}

export function contractStatusForTopic(
  contractKey: string,
): OwnerConfirmedValueStatus | "missing" {
  const input = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === contractKey);
  return input?.status ?? "missing";
}

export const RETURN_CANT_APPLY_PLAN_SAFETY = [
  "Workshop only — no Product Truth live write",
  "No Pricing activation",
  "No Work Intake exposure",
  "No runtime replacement",
  "No seed / live rows",
  "No values applied without explicit owner answer",
] as const;
