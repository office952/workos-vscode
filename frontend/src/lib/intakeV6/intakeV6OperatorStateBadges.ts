import type { LayerConfirmationState } from "@/lib/svgAnalyzer";
import { operatorStatusSemanticRo } from "@/lib/intakeV6/intakeV6OperatorVocabulary";

export type IntakeV6OperatorStateBadge =
  | "SUGGESTED"
  | "NEEDS_CONFIRMATION"
  | "NEEDS_FORM_INPUT"
  | "CONFIRMED"
  | "FALLBACK"
  | "BLOCKED"
  | "WARNING"
  | "READY";

export function resolveLayerConfirmationBadge(state: LayerConfirmationState | undefined): IntakeV6OperatorStateBadge {
  if (state === "confirmed") return "CONFIRMED";
  if (state === "ignored") return "READY";
  return "NEEDS_CONFIRMATION";
}

export function resolveHydratedFinishBadge(confirmed: boolean): IntakeV6OperatorStateBadge {
  return confirmed ? "CONFIRMED" : "FALLBACK";
}

export function resolveArtworkFinishBadges(args: {
  confirmed: boolean;
  hasTarget?: boolean;
}): IntakeV6OperatorStateBadge[] {
  if (args.hasTarget === false) return ["SUGGESTED", "BLOCKED", "NEEDS_FORM_INPUT"];
  if (args.confirmed) return ["SUGGESTED", "CONFIRMED"];
  return ["SUGGESTED", "NEEDS_CONFIRMATION", "FALLBACK"];
}

export function describeOperatorStateBadge(state: IntakeV6OperatorStateBadge): string {
  switch (state) {
    case "SUGGESTED":
      return operatorStatusSemanticRo("proposal");
    case "NEEDS_CONFIRMATION":
      return operatorStatusSemanticRo("needs_operator");
    case "NEEDS_FORM_INPUT":
      return operatorStatusSemanticRo("missing_data");
    case "CONFIRMED":
      return operatorStatusSemanticRo("confirmed");
    case "FALLBACK":
      return "Fallback/hydrated din template";
    case "BLOCKED":
      return operatorStatusSemanticRo("blocker");
    case "WARNING":
      return operatorStatusSemanticRo("warning");
    case "READY":
      return operatorStatusSemanticRo("ready");
  }
}
