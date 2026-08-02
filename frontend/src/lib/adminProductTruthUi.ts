export const ADMIN_TRUTH_FLOW_STEPS = [
  {
    id: "product",
    label: "Produs",
    description: "Structura și intenția produsului.",
  },
  {
    id: "templates",
    label: "Șabloane",
    description: "Ce poate exista; nu confirmă Product Truth runtime.",
  },
  {
    id: "pricing",
    label: "Prețuri",
    description: "Catalog și reguli; nu inventează tarife în șablon.",
  },
  {
    id: "equipment",
    label: "Utilaje",
    description: "Referință de capacitate, nu tarif client.",
  },
  {
    id: "settings",
    label: "Setări",
    description: "Configurație administrativă; politicile rămân în Guvernanță.",
  },
] as const;

export type AdminTruthFlowStepId = (typeof ADMIN_TRUTH_FLOW_STEPS)[number]["id"];

export function adminTruthFlowStep(
  id: AdminTruthFlowStepId,
): (typeof ADMIN_TRUTH_FLOW_STEPS)[number] {
  const step = ADMIN_TRUTH_FLOW_STEPS.find((candidate) => candidate.id === id);
  if (!step) {
    throw new Error(`Unknown admin truth flow step: ${id}`);
  }
  return step;
}
