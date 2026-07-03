/**
 * Documented canonical display names for operational material codes.
 * Mirrors backend/seeds/material_canonical_naming.py — no runtime DB writes.
 */

export type MaterialNamingCatalogEntry = {
  code: string;
  canonicalName: string;
  legacyRisk?: string;
};

/** High-risk / volumetric operational codes — cleanup target without code rename. */
export const MATERIAL_NAMING_CATALOG: readonly MaterialNamingCatalogEntry[] = [
  {
    code: "MAT-ACP-3MM",
    canonicalName: "Panou compozit aluminiu (ACM/ACP) 3 mm",
    legacyRisk: "Duplicate naming vs MAT-ACM-BOND-3MM",
  },
  {
    code: "MAT-ACM-BOND-3MM",
    canonicalName: "Panou compozit aluminiu (ACM/ACP) 3 mm",
  },
  {
    code: "MAT-ACM-BOND-4MM",
    canonicalName: "Panou compozit aluminiu (ACM/ACP) 4 mm",
  },
  {
    code: "MAT-ACM-BOND-PANEL",
    canonicalName: "Panou compozit aluminiu (ACM/ACP) — rezolvare grosime",
  },
  {
    code: "MAT-ACP-FATA-LITERE",
    canonicalName: "PMMA / plexiglas acrilic 3 mm — față litere",
    legacyRisk: "Code says ACP; stock is PMMA face",
  },
  {
    code: "MAT-SPATE-PVC-LITERE",
    canonicalName: "PVC expandat 10 mm",
    legacyRisk: "Forex is alias; code says PVC",
  },
  {
    code: "MAT-SABLON-MONTAJ",
    canonicalName: "PVC expandat 3 mm — șablon montaj",
  },
  {
    code: "MAT-PREMOUNT-BAR-STEEL",
    canonicalName: "Țeavă pătrată oțel 30×30×1.5 mm",
    legacyRisk: "PREMOUNT in code = usage",
  },
  {
    code: "MAT-PREMOUNT-BAR-ALUMINUM",
    canonicalName: "Țeavă pătrată aluminiu 30×30×1.5 mm",
  },
  {
    code: "MAT-ORACAL-651",
    canonicalName: "Folie autocolantă PVC — Oracal 651",
  },
  {
    code: "MAT_ORACAL_651",
    canonicalName: "Folie autocolantă PVC — Oracal 651",
    legacyRisk: "Product 001 namespace vs MAT-ORACAL-651",
  },
] as const;

export function getCatalogEntry(code: string): MaterialNamingCatalogEntry | undefined {
  return MATERIAL_NAMING_CATALOG.find((e) => e.code === code);
}
