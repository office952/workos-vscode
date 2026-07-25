/**
 * CNC processable badge — shared capability identifier (not decorative UI).
 *
 * Same badge id appears on:
 * - Letter-face plexi stock (MAT-ACP-FATA-LITERE)
 * - The specific CNC utilaj that processes it: CNC 4020 (MCH-CNC-4020)
 *
 * Do NOT attach by generic machine type (cnc_router) — polystyrene / other CNC
 * machines must not inherit this badge.
 *
 * Backend mirror: backend/services/cnc_processable_badge.py
 */

import {
  LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME,
  LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE,
} from "@/lib/materials/lettersFacePlexiMaterialDisplay";
import { CNC_LETTERS_FACE_SERVICES_RO } from "@/lib/cnc/cncProcessTaxonomyRo";

/** Short operator-facing mark (UI chip text). */
export const CNC_PROCESSABLE_BADGE_LABEL = "CNC";

/**
 * Stable capability identifier — use in docs, inventory, utilaje, Product System.
 * Do not invent parallel badges for the same meaning.
 */
export const CNC_PROCESSABLE_BADGE_CODE = "BADGE-CNC-PROCESSABLE";

export const CNC_PROCESSABLE_BADGE_TITLE_RO = "Procesabil CNC";

export const CNC_PROCESSABLE_BADGE_MEANING_RO =
  "Identificator de capacitate: plexiglas 3mm PMMA - opal (față litere) se prelucrează pe CNC 4020 — același badge pe material și pe acest utilaj.";

/** Inventory / pricing codes that carry the badge (Letters face stock only). */
export const CNC_PROCESSABLE_MATERIAL_CODES = [
  LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE, // MAT-ACP-FATA-LITERE
] as const;

/** Material this utilaj processes (Letters face stock) — display lock. */
export const CNC_PROCESSABLE_MATERIAL_DISPLAY_NAME = LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME;
export const CNC_PROCESSABLE_MATERIAL_REGISTRY_CODE = LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE;

/**
 * Only this utilaj carries the badge — not every cnc_router / polystyrene CNC.
 * Match by operational machine code (and common display aliases).
 */
export const CNC_PROCESSABLE_MACHINE_CODES = ["MCH-CNC-4020"] as const;

/**
 * Documented CNC services for letter-face plexi (shared with process strip).
 * Owner taxonomy: Decupare + Canal/Șanfren — not V-groove (that is Dibond fold).
 */
export const CNC_PROCESSABLE_LETTER_FACE_SERVICES = CNC_LETTERS_FACE_SERVICES_RO;

export type CncProcessableBadgeCarrier =
  | { kind: "material"; code: string }
  | { kind: "machine"; type?: string | null; id?: string | null; name?: string | null }
  | { kind: "workcenter"; code: string };

function normalizeCode(value: string | null | undefined): string {
  return String(value || "")
    .trim()
    .toUpperCase()
    .replace(/-/g, "_");
}

export function materialCarriesCncProcessableBadge(materialCode: string | null | undefined): boolean {
  const code = normalizeCode(materialCode).replace(/_/g, "-");
  return CNC_PROCESSABLE_MATERIAL_CODES.some((entry) => normalizeCode(entry).replace(/_/g, "-") === code);
}

/**
 * True only for CNC 4020 — never by broad type (cnc_router) or shared workcenter.
 */
export function machineCarriesCncProcessableBadge(args: {
  type?: string | null;
  id?: string | null;
  name?: string | null;
  workcenterCode?: string | null;
}): boolean {
  const id = normalizeCode(args.id);
  if (CNC_PROCESSABLE_MACHINE_CODES.some((code) => normalizeCode(code) === id)) {
    return true;
  }

  const name = String(args.name || "").trim().toUpperCase();
  if (!name) return false;

  // Prefer explicit "CNC 4020" / MCH-CNC-4020 in name; avoid bare "4020" alone
  // matching unrelated equipment — require CNC context or full code.
  if (name.includes("MCH-CNC-4020") || name.includes("MCH_CNC_4020")) return true;
  if (/\bCNC\s*4020\b/.test(name)) return true;
  if (name.includes("CNC") && name.includes("4020") && !/POLISTIREN|POLYSTYRENE|FOAM|EPS/i.test(name)) {
    return true;
  }

  return false;
}

export function carrierHasCncProcessableBadge(carrier: CncProcessableBadgeCarrier): boolean {
  switch (carrier.kind) {
    case "material":
      return materialCarriesCncProcessableBadge(carrier.code);
    case "machine":
      return machineCarriesCncProcessableBadge(carrier);
    case "workcenter":
      // Workcenter alone is not enough — polystyrene may share CNC routing WC.
      return false;
    default: {
      const _exhaustive: never = carrier;
      return _exhaustive;
    }
  }
}
