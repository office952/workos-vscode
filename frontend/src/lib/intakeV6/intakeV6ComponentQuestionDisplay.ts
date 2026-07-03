export type IntakeV6ComponentOwner =
  | "Face"
  | "Back"
  | "Return / Cant"
  | "Finish"
  | "Artwork"
  | "Electrical"
  | "Support"
  | "Mounting"
  | "Pricing boundary";

export type IntakeV6ComponentQuestionSourceStatus =
  | "FOUND_IN_EXISTING_FORM"
  | "FALLBACK_OR_HYDRATED"
  | "OPERATOR_CONFIRMABLE"
  | "OWNER_APPROVED_RULE_APPLIED"
  | "MISSING_UI_GAP";

export type IntakeV6ComponentQuestionBlockerLevel =
  | "REQUIRED_FOR_QUOTE"
  | "REQUIRED_FOR_ORDER"
  | "REQUIRED_FOR_EXECUTION"
  | "INTERNAL_ONLY"
  | "OPTIONAL_WARNING"
  | "QUOTE_BLOCKER_CONDITIONAL"
  | "ORDER_EXECUTION_ONLY";

export type IntakeV6ProductTruthCandidateStatus =
  | "PRODUCT_TRUTH_CANDIDATE"
  | "OWNER_APPROVED_DEFAULT"
  | "EXISTING_FORM_VALUE"
  | "FALLBACK_OR_HYDRATED"
  | "OPERATOR_CONFIRMABLE"
  | "NEEDS_OPERATOR_CONFIRMATION"
  | "CONFIRMED_TRUTH"
  | "NOT_PRODUCT_TRUTH"
  | "MISSING_UI_GAP";

export type IntakeV6ComponentQuestionKey =
  | "facePlexiglas"
  | "backForex"
  | "returnCant"
  | "finishOracalPrintLamination"
  | "artworkPrintedArtwork"
  | "electricalLedCables"
  | "supportBars"
  | "mountingScope"
  | "pricingBoundary";

export interface IntakeV6ComponentQuestionDisplayChip {
  text: string;
  tone: "owner" | "blocker" | "warning" | "info" | "internal";
}

export interface IntakeV6ComponentQuestionDisplay {
  key: IntakeV6ComponentQuestionKey;
  componentOwner: IntakeV6ComponentOwner;
  sourceStatus: IntakeV6ComponentQuestionSourceStatus[];
  blockerLevel: IntakeV6ComponentQuestionBlockerLevel[];
  productTruthStatus: IntakeV6ProductTruthCandidateStatus[];
  ownerApprovedRule: string;
  chips: IntakeV6ComponentQuestionDisplayChip[];
  displayOnly: true;
}

export const INTAKE_V6_COMPONENT_QUESTION_DISPLAY_ONLY_NOTE =
  "Display-only labels. These badges do not decide readiness, mutate form state, write payload, or unlock Review.";

export const INTAKE_V6_COMPONENT_QUESTION_DISPLAY: Record<
  IntakeV6ComponentQuestionKey,
  IntakeV6ComponentQuestionDisplay
> = {
  facePlexiglas: {
    key: "facePlexiglas",
    componentOwner: "Face",
    sourceStatus: ["FOUND_IN_EXISTING_FORM", "FALLBACK_OR_HYDRATED", "OPERATOR_CONFIRMABLE", "OWNER_APPROVED_RULE_APPLIED", "MISSING_UI_GAP"],
    blockerLevel: ["REQUIRED_FOR_QUOTE", "REQUIRED_FOR_ORDER", "REQUIRED_FOR_EXECUTION"],
    productTruthStatus: [
      "PRODUCT_TRUTH_CANDIDATE",
      "OWNER_APPROVED_DEFAULT",
      "OPERATOR_CONFIRMABLE",
      "NEEDS_OPERATOR_CONFIRMATION",
      "MISSING_UI_GAP",
    ],
    ownerApprovedRule: "plexiglas opal 3 mm default",
    chips: [
      { text: "Component: Face", tone: "info" },
      { text: "Product Truth candidate", tone: "info" },
      { text: "Required for quote", tone: "blocker" },
      { text: "Owner approved: plexiglas opal 3 mm default", tone: "owner" },
      { text: "Face material: plexiglas opal", tone: "owner" },
      { text: "Face thickness: 3 mm default", tone: "owner" },
      { text: "5 mm later exception", tone: "warning" },
      { text: "Owner-approved default, not final until confirmed", tone: "warning" },
      { text: "Operator confirmable", tone: "warning" },
      { text: "Missing UI gap: explicit face material/thickness control", tone: "warning" },
    ],
    displayOnly: true,
  },
  backForex: {
    key: "backForex",
    componentOwner: "Back",
    sourceStatus: ["FOUND_IN_EXISTING_FORM", "FALLBACK_OR_HYDRATED", "OPERATOR_CONFIRMABLE", "OWNER_APPROVED_RULE_APPLIED"],
    blockerLevel: ["REQUIRED_FOR_QUOTE", "REQUIRED_FOR_ORDER", "REQUIRED_FOR_EXECUTION"],
    productTruthStatus: [
      "PRODUCT_TRUTH_CANDIDATE",
      "OWNER_APPROVED_DEFAULT",
      "EXISTING_FORM_VALUE",
      "FALLBACK_OR_HYDRATED",
      "OPERATOR_CONFIRMABLE",
      "NEEDS_OPERATOR_CONFIRMATION",
    ],
    ownerApprovedRule: "Forex 10 mm, no sanfren default",
    chips: [
      { text: "Component: Back", tone: "info" },
      { text: "Product Truth candidate", tone: "info" },
      { text: "Existing form value", tone: "info" },
      { text: "Required for quote", tone: "blocker" },
      { text: "Owner approved: Forex 10 mm, no sanfren default", tone: "owner" },
      { text: "Back material: Forex 10 mm", tone: "owner" },
      { text: "No-sanfren default", tone: "owner" },
      { text: "Sanfren selectable", tone: "warning" },
      { text: "Fallback/hydrated until confirmed", tone: "warning" },
    ],
    displayOnly: true,
  },
  returnCant: {
    key: "returnCant",
    componentOwner: "Return / Cant",
    sourceStatus: ["FOUND_IN_EXISTING_FORM", "FALLBACK_OR_HYDRATED", "OPERATOR_CONFIRMABLE", "OWNER_APPROVED_RULE_APPLIED"],
    blockerLevel: ["REQUIRED_FOR_QUOTE", "REQUIRED_FOR_ORDER", "REQUIRED_FOR_EXECUTION"],
    productTruthStatus: [
      "PRODUCT_TRUTH_CANDIDATE",
      "EXISTING_FORM_VALUE",
      "FALLBACK_OR_HYDRATED",
      "OPERATOR_CONFIRMABLE",
      "NEEDS_OPERATOR_CONFIRMATION",
    ],
    ownerApprovedRule: "per group when different",
    chips: [
      { text: "Component: Return / Cant", tone: "info" },
      { text: "Product Truth candidate", tone: "info" },
      { text: "Existing form value", tone: "info" },
      { text: "Required for quote", tone: "blocker" },
      { text: "Per group when different", tone: "owner" },
      { text: "Depth, color, RAL, Oracal, vopsit selectable", tone: "owner" },
      { text: "Target: cant", tone: "info" },
      { text: "Fallback/hydrated until confirmed", tone: "warning" },
    ],
    displayOnly: true,
  },
  finishOracalPrintLamination: {
    key: "finishOracalPrintLamination",
    componentOwner: "Finish",
    sourceStatus: ["FOUND_IN_EXISTING_FORM", "FALLBACK_OR_HYDRATED", "OPERATOR_CONFIRMABLE", "OWNER_APPROVED_RULE_APPLIED", "MISSING_UI_GAP"],
    blockerLevel: ["REQUIRED_FOR_QUOTE", "REQUIRED_FOR_ORDER", "REQUIRED_FOR_EXECUTION"],
    productTruthStatus: [
      "PRODUCT_TRUTH_CANDIDATE",
      "EXISTING_FORM_VALUE",
      "FALLBACK_OR_HYDRATED",
      "OPERATOR_CONFIRMABLE",
      "NEEDS_OPERATOR_CONFIRMATION",
      "MISSING_UI_GAP",
    ],
    ownerApprovedRule: "print and lamination separate",
    chips: [
      { text: "Component: Finish", tone: "info" },
      { text: "Product Truth candidate", tone: "info" },
      { text: "Existing form answer", tone: "info" },
      { text: "Required for quote", tone: "blocker" },
      { text: "Print and lamination separate", tone: "owner" },
      { text: "Finish target required", tone: "blocker" },
      { text: "Oracal 641 / 651 / 8500 existing options", tone: "owner" },
      { text: "Target: fata / cant / artwork / spate", tone: "info" },
      { text: "Missing UI gap: separate print_required and lamination_required", tone: "warning" },
      { text: "Fallback/hydrated until confirmed", tone: "warning" },
    ],
    displayOnly: true,
  },
  artworkPrintedArtwork: {
    key: "artworkPrintedArtwork",
    componentOwner: "Artwork",
    sourceStatus: ["FOUND_IN_EXISTING_FORM", "FALLBACK_OR_HYDRATED", "OPERATOR_CONFIRMABLE", "OWNER_APPROVED_RULE_APPLIED", "MISSING_UI_GAP"],
    blockerLevel: ["REQUIRED_FOR_QUOTE", "REQUIRED_FOR_ORDER", "REQUIRED_FOR_EXECUTION"],
    productTruthStatus: [
      "PRODUCT_TRUTH_CANDIDATE",
      "FALLBACK_OR_HYDRATED",
      "OPERATOR_CONFIRMABLE",
      "NEEDS_OPERATOR_CONFIRMATION",
      "MISSING_UI_GAP",
    ],
    ownerApprovedRule: "suggestion is not final print",
    chips: [
      { text: "Component: Artwork", tone: "info" },
      { text: "Product Truth candidate", tone: "info" },
      { text: "Requires operator confirmation", tone: "blocker" },
      { text: "Suggestion is not final print", tone: "owner" },
      { text: "printed_artwork is suggestion", tone: "warning" },
      { text: "Choices: print/applied, artwork-only, ignored", tone: "warning" },
      { text: "Target: artwork", tone: "info" },
      { text: "Print required and lamination required stay separate", tone: "owner" },
    ],
    displayOnly: true,
  },
  electricalLedCables: {
    key: "electricalLedCables",
    componentOwner: "Electrical",
    sourceStatus: ["FOUND_IN_EXISTING_FORM", "FALLBACK_OR_HYDRATED", "OPERATOR_CONFIRMABLE", "OWNER_APPROVED_RULE_APPLIED"],
    blockerLevel: ["REQUIRED_FOR_ORDER", "REQUIRED_FOR_EXECUTION", "OPTIONAL_WARNING", "QUOTE_BLOCKER_CONDITIONAL", "ORDER_EXECUTION_ONLY"],
    productTruthStatus: [
      "PRODUCT_TRUTH_CANDIDATE",
      "OWNER_APPROVED_DEFAULT",
      "EXISTING_FORM_VALUE",
      "FALLBACK_OR_HYDRATED",
      "OPERATOR_CONFIRMABLE",
    ],
    ownerApprovedRule: "included defaults: 1 m 2x0.75 + 5 m 2x1.5",
    chips: [
      { text: "Component: Electrical", tone: "info" },
      { text: "Product Truth candidate", tone: "info" },
      { text: "Existing form value", tone: "info" },
      { text: "Included defaults: 1 m 2x0.75 + 5 m 2x1.5", tone: "owner" },
      { text: "Commercial default: 1 m cable 2x0.75 for letters", tone: "owner" },
      { text: "Commercial default: 5 m cable 2x1.5 final feed", tone: "owner" },
      { text: "Extra cables/site details: order/execution", tone: "warning" },
      { text: "Quote blocker conditional for special electrical/site scope", tone: "blocker" },
      { text: "Missing UI gap: cable routing and PSU placement", tone: "warning" },
    ],
    displayOnly: true,
  },
  supportBars: {
    key: "supportBars",
    componentOwner: "Support",
    sourceStatus: ["FOUND_IN_EXISTING_FORM", "OPERATOR_CONFIRMABLE", "OWNER_APPROVED_RULE_APPLIED", "MISSING_UI_GAP"],
    blockerLevel: ["REQUIRED_FOR_ORDER", "REQUIRED_FOR_EXECUTION", "OPTIONAL_WARNING", "QUOTE_BLOCKER_CONDITIONAL"],
    productTruthStatus: ["PRODUCT_TRUTH_CANDIDATE", "EXISTING_FORM_VALUE", "OPERATOR_CONFIRMABLE", "MISSING_UI_GAP"],
    ownerApprovedRule: "optional unless detected/suggested",
    chips: [
      { text: "Component: Support", tone: "info" },
      { text: "Product Truth candidate when support affects offer", tone: "info" },
      { text: "Optional unless detected/suggested", tone: "warning" },
      { text: "Ask/select if not detected in SVG", tone: "warning" },
      { text: "Required when affects offer", tone: "blocker" },
      { text: "Quote blocker conditional", tone: "blocker" },
      { text: "Missing UI gap: first-class support required/type/material", tone: "warning" },
      { text: "metal_support_required means Support/Bare, not mounting method", tone: "warning" },
      { text: "Support and mounting are separate decisions", tone: "warning" },
    ],
    displayOnly: true,
  },
  mountingScope: {
    key: "mountingScope",
    componentOwner: "Mounting",
    sourceStatus: ["FOUND_IN_EXISTING_FORM", "FALLBACK_OR_HYDRATED", "OPERATOR_CONFIRMABLE", "OWNER_APPROVED_RULE_APPLIED", "MISSING_UI_GAP"],
    blockerLevel: ["REQUIRED_FOR_QUOTE", "REQUIRED_FOR_ORDER", "REQUIRED_FOR_EXECUTION", "ORDER_EXECUTION_ONLY"],
    productTruthStatus: [
      "PRODUCT_TRUTH_CANDIDATE",
      "EXISTING_FORM_VALUE",
      "FALLBACK_OR_HYDRATED",
      "OPERATOR_CONFIRMABLE",
      "NEEDS_OPERATOR_CONFIRMATION",
      "MISSING_UI_GAP",
    ],
    ownerApprovedRule: "mounting scope explicit in offer",
    chips: [
      { text: "Component: Mounting", tone: "info" },
      { text: "Product Truth candidate", tone: "info" },
      { text: "Existing form value", tone: "info" },
      { text: "Required for quote when mounting included/external", tone: "blocker" },
      { text: "No mounting / included / external / to decide", tone: "owner" },
      { text: "mounting_system is Mounting, not Support truth", tone: "warning" },
      { text: "Order/execution for site and method details", tone: "warning" },
      { text: "Missing UI gap: included/external commercial scope control", tone: "warning" },
      { text: "Fallback/hydrated until confirmed", tone: "warning" },
    ],
    displayOnly: true,
  },
  pricingBoundary: {
    key: "pricingBoundary",
    componentOwner: "Pricing boundary",
    sourceStatus: ["FOUND_IN_EXISTING_FORM", "OWNER_APPROVED_RULE_APPLIED"],
    blockerLevel: ["INTERNAL_ONLY", "OPTIONAL_WARNING"],
    productTruthStatus: ["NOT_PRODUCT_TRUTH"],
    ownerApprovedRule: "Pricing Registry does not decide Product Truth",
    chips: [
      { text: "Component: Pricing boundary", tone: "info" },
      { text: "Not Product Truth", tone: "internal" },
      { text: "Product Truth first; pricing coverage after truth", tone: "owner" },
      { text: "Pricing Registry does not decide Product Truth", tone: "owner" },
      { text: "CostEngine internal-only", tone: "internal" },
    ],
    displayOnly: true,
  },
};

export function getIntakeV6ComponentQuestionDisplay(
  key: IntakeV6ComponentQuestionKey,
): IntakeV6ComponentQuestionDisplay {
  return INTAKE_V6_COMPONENT_QUESTION_DISPLAY[key];
}

export function getIntakeV6ComponentQuestionChips(
  key: IntakeV6ComponentQuestionKey,
): IntakeV6ComponentQuestionDisplayChip[] {
  return getIntakeV6ComponentQuestionDisplay(key).chips;
}