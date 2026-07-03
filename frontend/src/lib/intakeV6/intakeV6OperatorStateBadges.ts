import type { LayerConfirmationState } from "@/lib/svgAnalyzer";

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
      return "Sugerat de sistem";
    case "NEEDS_CONFIRMATION":
      return "Necesită confirmare";
    case "NEEDS_FORM_INPUT":
      return "Necesită input în formular";
    case "CONFIRMED":
      return "Confirmat operator";
    case "FALLBACK":
      return "Fallback/hydrated din template";
    case "BLOCKED":
      return "Blocat";
    case "WARNING":
      return "Warning";
    case "READY":
      return "Ready";
  }
}
