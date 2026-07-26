/**
 * Owner CNC process taxonomy (RO) — three separate elements (2026-07-23).
 *
 * Do not collapse V-groove into Canal/Șanfren. Do not invent a 4th family without GO.
 *
 * 1. Decupare — through-cut (any product that cuts contour)
 * 2. Canal / Șanfren — partial-depth groove/rabbet (letters face/edge bond path)
 * 3. V-groove — Dibond/ACM/Alucobond fold prep only (leaves ~0.8 mm skin)
 *
 * Sketches + links:
 *   docs/architecture/CNC_PROCESS_TAXONOMY_RO.md
 *   docs/worklog/realignment/audit_assets/24_acm_vgroove_fold_geometry.png
 *   docs/worklog/realignment/audit_assets/25_letters_canal_sanfren_section.png
 *   docs/worklog/realignment/audit_assets/26_letters_volumetric_section_confectionare.png
 *   docs/worklog/realignment/audit_assets/26_letters_litera_pe_layere_sectiune.png (alias)
 */

/** Canonical ordered list — all three CNC process families. */
export const CNC_PROCESS_ELEMENTS_RO = [
  "Decupare",
  "Canal / Șanfren",
  "V-groove",
] as const;

export type CncProcessElementRo = (typeof CNC_PROCESS_ELEMENTS_RO)[number];

/** Letters face plexi on CNC 4020 — elements 1 + 2 (not V-groove). */
export const CNC_LETTERS_FACE_SERVICES_RO = ["Decupare", "Canal / Șanfren"] as const;

/** Alucobond/Dibond casetat — elements 1 + 3 (not Canal/Șanfren for fold). */
export const CNC_ACM_BOXED_SERVICES_RO = ["Decupare", "V-groove"] as const;
