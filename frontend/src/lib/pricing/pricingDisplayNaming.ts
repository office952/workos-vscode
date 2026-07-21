/**
 * Display-only naming normalization for Pricing / Inventory labels.
 * Stable codes are never renamed here.
 */

const CODE_DISPLAY_OVERRIDES: Record<string, string> = {
  "MAT-ACP-FATA-LITERE": "Plexiglas / PMMA 3 mm — față litere (cod istoric ACP)",
  "MAT-ACM-BOND-3MM": "Panou compozit aluminiu (ACM/ACP) 3 mm",
  "MAT-ACM-BOND-4MM": "Panou compozit aluminiu (ACM/ACP) 4 mm",
  "MAT-ACM-BOND-PANEL": "Panou compozit aluminiu (ACM/ACP) — rezolvare grosime",
  "MAT-ACP-3MM": "Panou compozit aluminiu (ACM/ACP) 3 mm — alias legacy",
  CNC_ROUTER: "CNC router — debitare / tăiere",
  ACM_PANEL_CUTTING: "Debitare panou ACM",
  ACM_V_GROOVE: "Canelare V-groove ACM",
  LASER_CUTTING: "CNC laser — tăiere",
  FACE_VINYL_APPLICATION_LABOR: "Manoperă aplicare folie fețe",
  RETURN_CANT_VINYL_APPLICATION_LABOR: "Manoperă aplicare folie pe cant",
  RETURN_CANT_RAL_PAINT_LABOR: "Manoperă vopsire RAL pe cant",
  SITE_INSTALLATION_STANDARD: "Montaj la locație (standard)",
  LAMINATION: "Serviciu laminare",
  LARGE_FORMAT_PRINT: "Serviciu print format mare",
};

export function normalizePricingDisplayName(code: string, fallbackName: string): string {
  const c = String(code || "").trim().toUpperCase();
  if (CODE_DISPLAY_OVERRIDES[c]) return CODE_DISPLAY_OVERRIDES[c];
  return fallbackName || code;
}

export function misleadingCodeNoteRo(code: string): string | null {
  const c = String(code || "").trim().toUpperCase();
  if (c === "MAT-ACP-FATA-LITERE") {
    return "Cod istoric conține ACP, dar materialul este PMMA / plexiglas — nu panou ACM.";
  }
  if (c === "MAT-ACP-3MM") {
    return "Alias legacy pentru MAT-ACM-BOND-3MM — nu a doua opțiune de preț.";
  }
  return null;
}
