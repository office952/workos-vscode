/**
 * Nivel 1 UI vocabulary: Product Template → Modules (equal).
 *
 * Labels only — does NOT rename DB columns, API fields (`module_template_*`),
 * formulas, ProductAggregate semantics, CPP/EIC, or mini-module registry codes.
 */

export const PRODUCT_TEMPLATE_LABEL = "Product Template";

/** Primary composition slogan for catalog / candidate panels. */
export const PRODUCT_MODULES_SEMANTIC_LABEL = "1 Product Template + N Module produs egale";

export const MODULE_PRODUS_LABEL = "Module produs";
export const MODULE_TEHNIC_LABEL = "Modul tehnic";
export const MODULE_PRODUS_SHARED_LABEL = "Module produs partajate";
export const MODULE_PRODUS_BOUNDARY_LABEL = "Owner boundary: Module produs";
export const MODULE_PRODUS_CANDIDATE_SET_LABEL = "Candidate Module produs — Litere";
export const MODULE_PRODUS_LIST_HEADING = "Module produs";

/** Mini-module registry — operational packaging, not a product module. */
export const MINI_MODULE_OPERATIONAL_LABEL = "Mini-modul operațional";
export const MINI_MODULE_OPERATIONAL_EN_LABEL = "Operational mini-module";

export const PRODUCT_TEMPLATE_COMPOSES_HELP =
  "Product Template compune Module produs egale (față, cant/volum, spate, iluminare, structură, finisaj, montaj). Fiecare modul deține adevărul său tehnic. ProductAggregate rămâne read model derivat.";

export const PRODUCT_TEMPLATE_COMPOSER_ONLY_HELP =
  "Product Template este nivelul principal (composer). Modulele produsului sunt egale ca valoare structurală; acest panou arată ownership / gaps fără a inventa readiness.";

export const SHARED_FOUNDATION_HELP =
  "Contracte comune ca entități principale; Modulele produsului (rânduri child în product_templates + links) sunt binding-uri de profil. Mini-modulul operațional e separat. No pricing, no runtime activation, no Work Intake exposure change.";

export const CANDIDATE_COMPOSER_HELP =
  "Product Template candidat (readonly) — compune Module produs egale; nu e ofertabil în Work Intake.";

export const RETURN_CANT_MOVE_TRUTH_HELP =
  "Aliniere read-only pentru modulul cant/volum. Arată ce există deja, ce rămâne doar pe aggregate părinte și ce trebuie să fie adevăr pe Module produs — nu pe un sistem separat de template.";

export const MUST_OWN_ON_MODULE_LABEL = "Must own truth on Module produs";

/** Map legacy FE display tokens → Nivel 1 labels (internal keys may still use old wording). */
export function displayModuleSourceTypeLabel(sourceType: string): string {
  switch (sourceType) {
    case "component template / registry":
    case "module / registry":
      return "module / registry";
    case "component template":
    case "module produs":
      return "module produs";
    default:
      return sourceType;
  }
}

export function equalModulesHintRo(): string {
  return "Față, cant/volum și spate sunt Module produs egale — nu ierarhii nested de template.";
}
