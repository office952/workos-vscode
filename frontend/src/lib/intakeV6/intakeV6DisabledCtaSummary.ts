import type { IntakeV6StepId } from "./intakeV6Contracts";
import type { IntakeV6OperatorStateBadge } from "./intakeV6OperatorStateBadges";

export type IntakeV6DisabledCtaSummary = {
  badges: IntakeV6OperatorStateBadge[];
  title: string;
  message: string;
  submessage: string;
  nextAction: string;
  kind: "product_truth" | "pricing" | "warning";
};

function normalizedReason(reason: string | null | undefined): string {
  return (reason ?? "").toLowerCase();
}

function isProductTruthReason(reason: string): boolean {
  return (
    reason.includes("layer_roles_incomplete") ||
    reason.includes("confirmă rolul") ||
    reason.includes("confirma rolul") ||
    reason.includes("product truth") ||
    reason.includes("selected layer") ||
    reason.includes("finish target") ||
    reason.includes("artwork-only") ||
    reason.includes("artwork only") ||
    reason.includes("artwork") ||
    reason.includes("operator")
  );
}

function isFormInputReason(reason: string): boolean {
  return (
    reason.includes("selected layer") ||
    reason.includes("finish target") ||
    reason.includes("câmp") ||
    reason.includes("camp") ||
    reason.includes("formular")
  );
}

function isPricingCoverageReason(reason: string): boolean {
  return (
    reason.includes("tarif") ||
    reason.includes("preț") ||
    reason.includes("pret") ||
    reason.includes("pricing coverage") ||
    reason.includes("missing price") ||
    reason.includes("missing rate")
  );
}

export function resolveIntakeV6DisabledCtaSummary(args: {
  currentStep: IntakeV6StepId;
  disabled: boolean;
  reason?: string | null;
  layersTotal?: number | null;
  layersConfirmed?: number | null;
}): IntakeV6DisabledCtaSummary | null {
  if (!args.disabled) return null;
  const reason = normalizedReason(args.reason);
  if (!reason) return null;

  if (isProductTruthReason(reason)) {
    const badges: IntakeV6OperatorStateBadge[] = [
      "BLOCKED",
      isFormInputReason(reason) ? "NEEDS_FORM_INPUT" : "NEEDS_CONFIRMATION",
    ];
    const detectedText =
      args.layersTotal != null && args.layersTotal > 0
        ? `Există geometrie SVG și ${args.layersTotal} grupuri/straturi detectate; rolurile sunt doar sugerate${args.layersConfirmed != null ? ` (${args.layersConfirmed}/${args.layersTotal} confirmate)` : ""}.`
        : "Există geometrie SVG și roluri sugerate, dar Product Truth nu este confirmat complet.";

    return {
      badges,
      title: "Product Truth incomplet",
      message: "Rolurile layerelor/grupurilor trebuie confirmate de operator înainte de ofertă.",
      submessage: `Pricing Registry este pregătit; blocajul curent nu este de preț, ci de confirmare Product Truth. ${detectedText}`,
      nextAction: "Confirmă rolurile pentru toate grupurile detectate și deciziile de componentă.",
      kind: "product_truth",
    };
  }

  if (isPricingCoverageReason(reason)) {
    return {
      badges: ["WARNING", "NEEDS_FORM_INPUT"],
      title: "Pricing coverage de verificat",
      message: "Există linii cu tarif/preț neconfigurat în calculul disponibil.",
      submessage: "Acesta este un blocaj de acoperire pricing real, separat de confirmarea Product Truth.",
      nextAction: "Verifică liniile marcate cu tarif lipsă înainte de draft.",
      kind: "pricing",
    };
  }

  return {
    badges: ["WARNING"],
    title: "Acțiune necesară",
    message: args.reason ?? "CTA-ul este blocat până la finalizarea verificărilor.",
    submessage: "Verifică pașii marcați în Intake V6 înainte de continuare.",
    nextAction: args.currentStep === "confirm" ? "Rezolvă blockerul afișat în Confirmare." : "Rezolvă blockerul afișat în pasul curent.",
    kind: "warning",
  };
}
