/**
 * Execution flow UI helpers — Comenzi → Execuție → Atelier → Control producție.
 * Presentation-only: labels, continuity links, compact next-step copy.
 * Does not invent scheduling, claiming, costs, or mutations.
 */

export type ExecutionFlowStage =
  | "comenzi"
  | "executie"
  | "atelier"
  | "control"
  | "operator";

export const EXECUTION_FLOW_STAGES: ReadonlyArray<{
  id: Exclude<ExecutionFlowStage, "operator">;
  label: string;
  path: string;
}> = [
  { id: "comenzi", label: "Comenzi", path: "/orders" },
  { id: "executie", label: "Execuție", path: "/execution" },
  { id: "atelier", label: "Atelier", path: "/shop-floor" },
  { id: "control", label: "Control producție", path: "/dashboard" },
] as const;

export function executionFlowStageIndex(
  stage: ExecutionFlowStage,
): number {
  if (stage === "operator") {
    // Compatibility surface sits beside Atelier, not a fifth canonical step.
    return EXECUTION_FLOW_STAGES.findIndex((s) => s.id === "atelier");
  }
  return EXECUTION_FLOW_STAGES.findIndex((s) => s.id === stage);
}

export type ExecutionNextStepHint = {
  title: string;
  description: string;
  primaryLabel?: string;
  primaryTo?: string;
  secondaryLabel?: string;
  secondaryTo?: string;
};

/** List-level hint — no order context. */
export function executionListNextStepHint(): ExecutionNextStepHint {
  return {
    title: "Următorul pas: Deschide o comandă în execuție",
    description:
      "Alege o comandă pentru a vedea planul, readiness-ul, taskurile și actualele. Atelierul și Controlul producție rămân vederi agregate.",
    primaryLabel: "Vezi Atelier",
    primaryTo: "/shop-floor",
    secondaryLabel: "Control producție",
    secondaryTo: "/dashboard",
  };
}

/** Order-scoped detail hint — links only; no invented actions. */
export function executionDetailNextStepHint(
  orderId: number | null,
): ExecutionNextStepHint {
  const operatorTo =
    orderId != null && Number.isInteger(orderId)
      ? `/operator?orderId=${orderId}`
      : "/operator";
  return {
    title: "Următorul pas: Urmărește taskurile și realitatea sesiunilor",
    description:
      "Planificat și actual rămân separate. Pornirea lucrului necesită identitate demonstrată pe backend — fără employee_id manual din browser. Atelierul arată ce e pregătit/blocat; Controlul agregă excepțiile.",
    primaryLabel: "Vezi Atelier",
    primaryTo: "/shop-floor",
    secondaryLabel: "Operator (compatibilitate)",
    secondaryTo: operatorTo,
  };
}

export function shopFloorNextStepHint(): ExecutionNextStepHint {
  return {
    title: "Următorul pas: Acționează pe task",
    description:
      "Atelierul este monitorizare. Start/Complete rămân pe Acțiune task / Stații, cu poarta de identitate pe backend. Controlul producție rămâne agregat de management.",
    primaryLabel: "Acțiune task",
    primaryTo: "/operator",
    secondaryLabel: "Stații",
    secondaryTo: "/tablet",
  };
}

export function controlProductionNextStepHint(): ExecutionNextStepHint {
  return {
    title: "Următorul pas: Investighează excepțiile în Execuție / Atelier",
    description:
      "Controlul producție agregă riscuri și gap-uri. Detaliul de comandă și taskurile rămân în Execuție; acțiunea de task în Operator.",
    primaryLabel: "Deschide Execuție",
    primaryTo: "/execution",
    secondaryLabel: "Vezi Atelier",
    secondaryTo: "/shop-floor",
  };
}

export function operatorCompatibilityHint(
  orderId: number | null,
): ExecutionNextStepHint {
  const executionTo =
    orderId != null && Number.isInteger(orderId)
      ? `/execution/${orderId}`
      : "/execution";
  return {
    title: "Compatibilitate Operator / Tablet",
    description:
      "Această suprafață rămâne pentru acțiunea pe task. Nu inventează scheduling sau claiming. Identitatea angajatului asignat trebuie demonstrată — fără impersonare.",
    primaryLabel: "Înapoi la Execuție",
    primaryTo: executionTo,
    secondaryLabel: "Vezi Atelier",
    secondaryTo: "/shop-floor",
  };
}
