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
    canonicalName: "Panou compozit aluminiu (ACM/ACP) 3 mm — legacy alias",
    legacyRisk: "Legacy alias of MAT-ACM-BOND-3MM — not a second technical/pricing option",
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
    canonicalName: "plexiglas 3mm PMMA - opal",
    legacyRisk: "Code says ACP; stock is plexiglas 3mm PMMA - opal (owner display lock 2026-07-23)",
  },
  {
    code: "MAT-SPATE-PVC-LITERE",
    canonicalName: "Forex 10 mm",
    legacyRisk: "Code says PVC; owner display lock 2026-07-23 = Forex 10 mm (PVC expandat)",
  },
  {
    code: "MAT-LED-MODULE",
    canonicalName: "Modul LED 12V",
  },
  {
    code: "MAT-LED-STRIP",
    canonicalName: "Bandă LED 12V",
    legacyRisk: "Alternative to modules (led_strip), not the letters standard",
  },
  {
    code: "MAT-LED-PSU-12V",
    canonicalName: "Sursă LED 12V — alege puterea (60/100/160/200 W)",
    legacyRisk: "Selector — not a single purchase SKU",
  },
  {
    code: "MAT-LED-PSU-12V-60W",
    canonicalName: "Sursă LED 12V 60W",
  },
  {
    code: "MAT-LED-PSU-12V-100W",
    canonicalName: "Sursă LED 12V 100W",
  },
  {
    code: "MAT-LED-PSU-12V-160W",
    canonicalName: "Sursă LED 12V 160W",
  },
  {
    code: "MAT-LED-PSU-12V-200W",
    canonicalName: "Sursă LED 12V 200W",
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
    code: "MAT-ORACAL-641",
    canonicalName: "Oracal 641",
  },
  {
    code: "MAT-ORACAL-651",
    canonicalName: "Oracal 651",
  },
  {
    code: "MAT-ORACAL-8500",
    canonicalName: "Oracal 8500",
  },
  {
    code: "MAT-VINYL-PRINT-LAMINATED",
    canonicalName: "Printat / Laminat",
  },
  {
    code: "MAT_ORACAL_651",
    canonicalName: "Oracal 651",
    legacyRisk: "Product 001 namespace vs MAT-ORACAL-651",
  },
] as const;

export function getCatalogEntry(code: string): MaterialNamingCatalogEntry | undefined {
  return MATERIAL_NAMING_CATALOG.find((e) => e.code === code);
}
