/**
 * Principal production task order for volumetric letters — display SoT on Structure cards.
 * Cards = components; this module = how you obtain them (tasks). Not ExecutionPlan authority.
 *
 * Distilled from owner TASK_LOGIC (no shared support) + memoriu T01–T19E + process graph.
 * Scope: letters only, no shared rear support, no emblem.
 *
 * Mirror: docs/worklog/realignment/2026-07-23_letters_structure_principal_task_order.md
 */

import type { LettersStructureStepId } from "./lettersStructureDetailRoutes";
import {
  LETTERS_STRUCTURE_STEP_CAPAC_SPATE,
  LETTERS_STRUCTURE_STEP_SISTEM_LED,
  LETTERS_STRUCTURE_STEP_VIZUAL_FATA,
  LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU,
} from "./lettersStructureDetailRoutes";

export type LettersPrincipalTaskId =
  | "prep_vector"
  | "prep_cnc_file"
  | "cut_face"
  | "cut_forex_back"
  | "prep_cant_path"
  | "apply_cant_vinyl"
  | "form_cant"
  | "bond_face_cant"
  | "paint_cant_ral"
  | "install_led"
  | "wire_test_led"
  | "attach_body_to_back"
  | "face_finish_after_assembly"
  | "pack_with_psu";

export type LettersPrincipalTask = {
  id: LettersPrincipalTaskId;
  /** 1-based display order in the principal chain. */
  order: number;
  labelRo: string;
  meaningRo: string;
  /** Structure components this task helps obtain or finish. */
  componentStepIds: readonly LettersStructureStepId[];
  /** Soft condition — shown as note, not a separate product truth write. */
  conditionRo?: string;
  /** Late / after assembly — still listed so the 4 cards explain the full letter chain. */
  lateRo?: boolean;
};

/** Full principal chain — same list on every structure detail page. */
export const LETTERS_PRINCIPAL_TASK_CHAIN: readonly LettersPrincipalTask[] = [
  {
    id: "prep_vector",
    order: 1,
    labelRo: "Pregătire grafică vectorială (față + Forex)",
    meaningRo:
      "Fără vector valid nu există nici față plexi, nici capac Forex. Pregătire comună pentru ambele debitări.",
    componentStepIds: [
      LETTERS_STRUCTURE_STEP_VIZUAL_FATA,
      LETTERS_STRUCTURE_STEP_CAPAC_SPATE,
    ],
  },
  {
    id: "prep_cnc_file",
    order: 2,
    labelRo: "Pregătire fișier CNC (ArtCAM / DWG debitare)",
    meaningRo:
      "Fișier specific mașină pentru debitare față și spate — operație tehnică separată de grafica vectorială.",
    componentStepIds: [
      LETTERS_STRUCTURE_STEP_VIZUAL_FATA,
      LETTERS_STRUCTURE_STEP_CAPAC_SPATE,
    ],
  },
  {
    id: "cut_face",
    order: 3,
    labelRo: "Alege material față cf. comandă + debitare CNC față (+ șanfren)",
    meaningRo:
      "Obține piesa Vizual față. Șanfren pe calea standard pentru lipirea volumului.",
    componentStepIds: [LETTERS_STRUCTURE_STEP_VIZUAL_FATA],
  },
  {
    id: "cut_forex_back",
    order: 4,
    labelRo: "Alege Forex 10 mm cf. comandă + debitare CNC spate (± șanfren)",
    meaningRo:
      "Obține Capac spate. Poate rula în paralel cu CNC față după fișierul CNC. Șanfren spate = opțional.",
    componentStepIds: [LETTERS_STRUCTURE_STEP_CAPAC_SPATE],
  },
  {
    id: "prep_cant_path",
    order: 5,
    labelRo: "Pregătire traseu / fișier modelare cant",
    meaningRo: "Pregătire tehnică pentru formare profil aluminiu (Volum).",
    componentStepIds: [LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU],
  },
  {
    id: "apply_cant_vinyl",
    order: 6,
    labelRo: "Colantare cant (Oracal) înainte de modelare",
    meaningRo: "La banc — doar dacă finisajul cantului e colantat. Nu la CNC.",
    componentStepIds: [LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU],
    conditionRo: "Doar dacă return_finish = Oracal / colantat",
  },
  {
    id: "form_cant",
    order: 7,
    labelRo: "Formare / modelare cant aluminiu",
    meaningRo: "Obține volumul format. Depinde de prep traseu; dacă Oracal — după colantare cant.",
    componentStepIds: [LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU],
  },
  {
    id: "bond_face_cant",
    order: 8,
    labelRo: "Lipire volum pe față (șanfren)",
    meaningRo: "Leagă Vizual față + Volum. Necesită față debitată (+ șanfren) și cant format.",
    componentStepIds: [
      LETTERS_STRUCTURE_STEP_VIZUAL_FATA,
      LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU,
    ],
  },
  {
    id: "paint_cant_ral",
    order: 9,
    labelRo: "Vopsire RAL pe cant după lipire",
    meaningRo: "Doar pe calea cant vopsit — după lipirea volumului pe față.",
    componentStepIds: [LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU],
    conditionRo: "Doar dacă return_finish = RAL / vopsit",
  },
  {
    id: "install_led",
    order: 10,
    labelRo: "Montaj module LED pe Forex",
    meaningRo:
      "Necesită Capac spate deja debitat. Doar litere — emblema e tratament separat.",
    componentStepIds: [LETTERS_STRUCTURE_STEP_SISTEM_LED, LETTERS_STRUCTURE_STEP_CAPAC_SPATE],
  },
  {
    id: "wire_test_led",
    order: 11,
    labelRo: "Cablare LED + test aprindere + alocare PSU",
    meaningRo:
      "PSU din puterea LED litere (rezervă 30%, trepte 60/100/160/200; multi-sursă dacă e nevoie).",
    componentStepIds: [LETTERS_STRUCTURE_STEP_SISTEM_LED],
  },
  {
    id: "attach_body_to_back",
    order: 12,
    labelRo: "Prindere corp literă pe spate Forex",
    meaningRo: "Asamblare după LED pe Forex și după corp (față+volum) gata.",
    componentStepIds: [
      LETTERS_STRUCTURE_STEP_CAPAC_SPATE,
      LETTERS_STRUCTURE_STEP_VIZUAL_FATA,
      LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU,
      LETTERS_STRUCTURE_STEP_SISTEM_LED,
    ],
  },
  {
    id: "face_finish_after_assembly",
    order: 13,
    labelRo: "Finisaj față (Oracal / print) după asamblare",
    meaningRo:
      "Nu e proces CNC pe plexi. Se aplică pe fața deja în corp — task târziu, documentat pe cardul Vizual față.",
    componentStepIds: [LETTERS_STRUCTURE_STEP_VIZUAL_FATA],
    lateRo: true,
  },
  {
    id: "pack_with_psu",
    order: 14,
    labelRo: "Colet / ambalare — surse PSU în colet",
    meaningRo: "Fără suport comun: PSU nu se montează pe suport atelier; merg în colet.",
    componentStepIds: [LETTERS_STRUCTURE_STEP_SISTEM_LED],
    lateRo: true,
  },
] as const;

export const LETTERS_PRINCIPAL_TASK_CHAIN_INTRO_RO =
  "Cardurile de structură sunt componente. Mai jos e ordinea taskurilor prin care le obții (fără suport comun, fără emblemă).";

export const LETTERS_STRUCTURE_CARD_NOT_TASK_HELPER_RO =
  "Ordinea taskurilor e pe fiecare pagină de componentă — card ≠ task.";

export type LettersComponentObtainDoc = {
  stepId: LettersStructureStepId;
  titleRo: string;
  withoutTheseRo: string;
  principalTaskIds: readonly LettersPrincipalTaskId[];
  notesRo: readonly string[];
};

/** How you obtain each structure component — principal tasks only. */
export const LETTERS_COMPONENT_OBTAIN_DOCS: readonly LettersComponentObtainDoc[] = [
  {
    stepId: LETTERS_STRUCTURE_STEP_VIZUAL_FATA,
    titleRo: "Cum obții Vizual față",
    withoutTheseRo: "Fără grafica vectorială și fără debitarea CNC nu există față.",
    principalTaskIds: ["prep_vector", "prep_cnc_file", "cut_face"],
    notesRo: [
      "Finisaj Oracal / print pe față = task târziu, după asamblarea corpului (nu obține piesa CNC).",
      "Șanfren față = pe calea standard, pentru lipirea volumului.",
    ],
  },
  {
    stepId: LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU,
    titleRo: "Cum obții Volum aluminiu",
    withoutTheseRo: "Fără formare cant (și lipire pe față) nu există volum pe literă.",
    principalTaskIds: ["prep_cant_path", "apply_cant_vinyl", "form_cant", "bond_face_cant"],
    notesRo: [
      "Oracal pe cant: înainte de modelare (condiționat).",
      "RAL pe cant: după lipirea pe față (condiționat).",
      "Consumă perimetrul din Vizual față — nu inventează geometrie.",
    ],
  },
  {
    stepId: LETTERS_STRUCTURE_STEP_CAPAC_SPATE,
    titleRo: "Cum obții Capac spate Forex",
    withoutTheseRo: "Fără aceeași prep vector/CNC și fără debitarea Forex nu există spate.",
    principalTaskIds: ["prep_vector", "prep_cnc_file", "cut_forex_back"],
    notesRo: [
      "Prep vector + fișier CNC sunt comune cu fața; debitarea Forex e taskul care produce spatele.",
      "Șanfren spate = opțional (default owner: fără).",
      "LED se montează pe acest Forex după debitare — nu pe această listă de obținere.",
    ],
  },
  {
    stepId: LETTERS_STRUCTURE_STEP_SISTEM_LED,
    titleRo: "Cum obții Sistem LED (litere)",
    withoutTheseRo: "Fără Forex debitat nu ai pe ce monta modulele; fără montaj/cablare nu ai iluminare.",
    principalTaskIds: ["install_led", "wire_test_led", "pack_with_psu"],
    notesRo: [
      "Doar litere — emblema pe densitate mp e tratament separat.",
      "PSU: alocare automată din puterea LED litere; în colet dacă nu e suport comun.",
    ],
  },
] as const;

export function getLettersPrincipalTaskById(
  id: LettersPrincipalTaskId,
): LettersPrincipalTask | undefined {
  return LETTERS_PRINCIPAL_TASK_CHAIN.find((task) => task.id === id);
}

export function getLettersComponentObtainDoc(
  stepId: LettersStructureStepId,
): LettersComponentObtainDoc | undefined {
  return LETTERS_COMPONENT_OBTAIN_DOCS.find((doc) => doc.stepId === stepId);
}

export function isTaskOwnedByComponent(
  task: LettersPrincipalTask,
  stepId: LettersStructureStepId,
): boolean {
  return task.componentStepIds.includes(stepId);
}

export function listObtainTasksForComponent(
  stepId: LettersStructureStepId,
): readonly LettersPrincipalTask[] {
  const doc = getLettersComponentObtainDoc(stepId);
  if (!doc) return [];
  return doc.principalTaskIds
    .map((id) => getLettersPrincipalTaskById(id))
    .filter((task): task is LettersPrincipalTask => task != null);
}
