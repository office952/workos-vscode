/**
 * OFERTA_VS_COST_INTERN_INTAKE_CHROME_V1 — display vocabulary only.
 * Does not change CPP/EIC formulas, API contracts, or calculated values.
 */

export const OFERTA_CLIENT_LABEL = "Ofertă client";
export const OFERTA_CLIENT_CHIP_LABEL = "Preț pentru client";
export const OFERTA_CLIENT_HELP =
  "Valoare comercială destinată clientului (CPP / Snapshot V2). Nu este cost de atelier.";

export const COST_INTERN_ESTIMATIV_LABEL = "Cost intern estimativ";
export const COST_INTERN_HELP =
  "Estimare internă pentru atelier / marjă (EIC / breakdown). Nu înlocuiește Oferta client.";

export const REGISTRY_INTERN_LABEL = "Registry intern";
export const REGISTRY_INTERN_HELP =
  "Catalog de referință (Pricing / Utilaje / Pontaj) — helper pentru calcul/analiză, nu fluxul principal de ofertare.";

export const OFERTA_VS_COST_BOUNDARY_HELP =
  "Ofertă client = ce plătește clientul. Cost intern estimativ = referință atelier. Registries = inputuri admin, nu pași operator.";

export const DO_NOT_EDIT_REGISTRY_IN_OFFER_FLOW_HELP =
  "Nu modifica registries în timpul ofertării — folosește valorile calculate din Ofertă client.";
