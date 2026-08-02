/**
 * Commercial flow UI helpers — Cereri → Produse → Oferte → Comenzi.
 * Presentation-only: labels, next-step copy, and continuity links.
 * Does not invent business truth, gates, or mutations.
 */

export type CommercialFlowStage = "cereri" | "produse" | "oferte" | "comenzi";

export const COMMERCIAL_FLOW_STAGES: ReadonlyArray<{
  id: CommercialFlowStage;
  label: string;
  path: string;
}> = [
  { id: "cereri", label: "Cereri", path: "/intake" },
  { id: "produse", label: "Produse", path: "/product-system/products" },
  { id: "oferte", label: "Oferte", path: "/quotes" },
  { id: "comenzi", label: "Comenzi", path: "/orders" },
] as const;

export function commercialFlowStageIndex(stage: CommercialFlowStage): number {
  return COMMERCIAL_FLOW_STAGES.findIndex((s) => s.id === stage);
}

/** Romanian operator labels for quote status — EN codes stay in StatusBadge domain. */
export function quoteStatusLabelRo(status: string): string {
  switch (status) {
    case "draft":
      return "Ciornă";
    case "priced":
      return "Tarifat";
    case "sent":
      return "Trimis";
    case "viewed":
      return "Vizualizat";
    case "negotiating":
      return "Negociere";
    case "accepted":
      return "Acceptat";
    case "rejected":
      return "Respins";
    case "expired":
      return "Expirat";
    default:
      return status || "Necunoscut";
  }
}

export type CommercialNextStepHint = {
  title: string;
  description: string;
  primaryLabel?: string;
  primaryTo?: string;
  secondaryLabel?: string;
  secondaryTo?: string;
};

/** Contextual next-step copy for the Cereri list detail panel (no auto-actions). */
export function intakeListNextStepHint(status: string): CommercialNextStepHint {
  switch (status) {
    case "new":
      return {
        title: "Următorul pas: Deschide cererea",
        description:
          "Preia cererea în analiză și configurează produsul înainte de ofertă.",
        primaryLabel: "Configurează produsul",
        primaryTo: "/product-system/products",
        secondaryLabel: "Vezi produse",
        secondaryTo: "/product-system/products",
      };
    case "in_review":
    case "needs_info":
      return {
        title: "Următorul pas: Completează produsul",
        description:
          "Definirea produsului și datele lipsă se rezolvă în spațiul de lucru al cererii. Apoi poți trece la ofertă.",
        primaryLabel: "Vezi produse",
        primaryTo: "/product-system/products",
        secondaryLabel: "Vezi oferte",
        secondaryTo: "/quotes",
      };
    case "ready_for_quote":
      return {
        title: "Următorul pas: Creează / continuă oferta",
        description:
          "Cererea este gata pentru ofertă. Folosește acțiunea din panou — nu se creează automat.",
        primaryLabel: "Deschide oferte",
        primaryTo: "/quotes",
        secondaryLabel: "Vezi produse",
        secondaryTo: "/product-system/products",
      };
    case "blocked":
      return {
        title: "Cerere blocată",
        description:
          "Rezolvați blocajul din spațiul cererii înainte de ofertă. Diagnosticul detaliat rămâne secundar.",
        primaryLabel: "Vezi produse",
        primaryTo: "/product-system/products",
      };
    case "cancelled":
      return {
        title: "Cerere anulată",
        description: "Nu există pas comercial următor pentru o cerere anulată.",
        secondaryLabel: "Înapoi la listă",
        secondaryTo: "/intake",
      };
    default:
      return {
        title: "Flux comercial",
        description: "Cerere → Produs → Ofertă → Comandă. Alege o cerere pentru pasul următor.",
        primaryLabel: "Vezi produse",
        primaryTo: "/product-system/products",
        secondaryLabel: "Vezi oferte",
        secondaryTo: "/quotes",
      };
  }
}

export function productsNextStepHint(): CommercialNextStepHint {
  return {
    title: "Următorul pas: Continuă spre ofertă",
    description:
      "Produsele și template-urile definesc ce se poate oferi. Oferta se creează din Cereri / Oferte — nu din acest ecran.",
    primaryLabel: "Deschide oferte",
    primaryTo: "/quotes",
    secondaryLabel: "Înapoi la cereri",
    secondaryTo: "/intake",
  };
}
