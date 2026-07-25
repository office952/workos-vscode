import {
  CNC_PROCESSABLE_BADGE_CODE,
  CNC_PROCESSABLE_LETTER_FACE_SERVICES,
} from "@/lib/cnc/cncProcessableBadge";
import { LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME } from "@/lib/materials/lettersFacePlexiMaterialDisplay";

/**
 * Letters FACE — documented process strip only.
 * Sources (no invention):
 * - docs/worklog/owner-input/face_component_truth_owner_decision_v1.md (§A, §B, §E)
 * - backend/services/shared_cnc_operation_model.py (VOLUMETRIC_FACE_CUTTING_RULE, VOLUMETRIC_FACE_BEVEL_RULE)
 * - frontend/.../volumetricLettersProduction.ts (șanfren față for bond)
 * - FACE does not own vinyl/print (FINISH) — face_component_truth_owner_decision_v1.md §G
 * - Material display lock: lettersFacePlexiMaterialDisplay.ts
 * - CNC badge identifier: cncProcessableBadge.ts (`BADGE-CNC-PROCESSABLE`)
 */

export type LettersFaceProcessStep = {
  id: string;
  labelRo: string;
  sourceNote: string;
};

/** Standard path: plexiglas 3mm PMMA - opal → considered Vizual față (substrate). */
export const LETTERS_FACE_PLEXI_3MM_PROCESS: readonly LettersFaceProcessStep[] = [
  {
    id: "material_plexi_3mm",
    labelRo: LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME,
    sourceNote:
      `Owner display lock 2026-07-23 + face_component_truth_owner_decision_v1 §A–B — FACE standard 3 mm opal; carries ${CNC_PROCESSABLE_BADGE_CODE}`,
  },
  {
    id: "cnc_debitare",
    labelRo: "Decupare CNC (router)",
    sourceNote:
      "Owner CNC taxonomy 2026-07-23 element 1 + face_component_truth §E + shared_cnc VOLUMETRIC_FACE_CUTTING_RULE",
  },
  {
    id: "cnc_sanfren",
    labelRo: "Canal / Șanfren CNC față",
    sourceNote:
      "Owner CNC taxonomy element 2 (litere) + shared_cnc VOLUMETRIC_FACE_BEVEL_RULE — canal pe margine/suprafață pentru lipire volum; ≠ V-groove Dibond",
  },
] as const;

/** CNC hover copy — title + numbered services (same as badge contract). */
export const LETTERS_FACE_CNC_TOOLTIP_TITLE = "Procesare CNC";

export const LETTERS_FACE_CNC_SERVICES: readonly string[] = CNC_PROCESSABLE_LETTER_FACE_SERVICES;

export function isLettersFaceStructureComponent(component: {
  type: string;
  component_id: string;
  name: string;
}): boolean {
  const key = `${component.component_id} ${component.name}`
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
  if (key.includes("face") || key.includes("fata") || key.includes("vizual")) {
    return true;
  }
  return false;
}
