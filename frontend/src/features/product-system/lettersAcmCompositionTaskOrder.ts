/**
 * Letters↔ACM composition — ACM surface delta of the shared letters mounting spine.
 * Not ExecutionPlan authority. Does not replace standalone Letters or ACM chains.
 *
 * Shared spine = memoriu T12–T18 (șablon → Forex pe suport → electric → test → corp → pack).
 * Same model as bare/premount; this file only names the Alucobond locus.
 * Cables: PH2-OD-09 (not reinvented here).
 *
 * OWNER_CONFIRMED 2026-07-23 + unity AMEND:
 * A Alucobond final fără pack → B șablon (20 EUR/mp outbox integral) →
 * C Forex+electric pe bond → D corp pe Forex → E pack ansamblu.
 *
 * Mirror: docs/architecture/product-system/LETTERS_ACM_COMPATIBILITY_CONTRACT_V1.md
 */

import {
  formatLettersAcmSablonProcessRateRo,
  LETTERS_ACM_SABLON_AREA_BASIS_RO,
  LETTERS_ACM_SABLON_BUNDLED_STEPS_RO,
  LETTERS_ACM_SABLON_PROCESS_LABEL_RO,
  LETTERS_ACM_SABLON_PROCESS_MEANING_RO,
} from "./lettersAcmCompositionSablonProcess";

export type LettersAcmCompositionTaskId =
  | "acm_finish_no_pack"
  | "sablon_process_on_bond"
  | "fasten_forex_on_bond"
  | "electric_inside_bond_psu"
  | "supply_cable_5m_220v"
  | "light_test"
  | "attach_body_to_forex_on_bond"
  | "pack_composite";

export type LettersAcmCompositionTask = {
  id: LettersAcmCompositionTaskId;
  order: number;
  labelRo: string;
  meaningRo: string;
  conditionRo?: string;
  /** Commercial teaching note — not an offer write. */
  costNoteRo?: string;
};

export const LETTERS_ACM_COMPOSITION_TASK_CHAIN: readonly LettersAcmCompositionTask[] = [
  {
    id: "acm_finish_no_pack",
    order: 1,
    labelRo: "Finalizează Alucobond casetat (fără impachetare)",
    meaningRo:
      "Lanț ACM 1–9: ArtCAM → V-groove → debitare → pliere → cadru → prindere → colant XOR vopsire șuruburi → accesorii montaj. Pack ACM se amână până la finalul ansamblului.",
    conditionRo: "Composition Litere pe ACM — nu pack standalone ACM înainte de montaj litere",
  },
  {
    id: "sablon_process_on_bond",
    order: 2,
    labelRo: LETTERS_ACM_SABLON_PROCESS_LABEL_RO,
    meaningRo: [
      LETTERS_ACM_SABLON_PROCESS_MEANING_RO,
      `Pași atelier (nu linii de cost): ${LETTERS_ACM_SABLON_BUNDLED_STEPS_RO.join(" · ")}.`,
      `Zonă mp: ${LETTERS_ACM_SABLON_AREA_BASIS_RO}`,
    ].join(" "),
    costNoteRo: formatLettersAcmSablonProcessRateRo(),
  },
  {
    id: "fasten_forex_on_bond",
    order: 3,
    labelRo: "Prindere spate Forex pe bond cu autoforante",
    meaningRo:
      "Forex-urile literelor — cu LED și cabluri jumper deja pregătite — se prind pe Alucobond folosind șablonul ca ghidaj. Formele pline rămân sub Forex.",
  },
  {
    id: "electric_inside_bond_psu",
    order: 4,
    labelRo: "Electrică în interiorul carcasei bond + legare transformator",
    meaningRo:
      "Trasee și legături în interiorul carcasei Alucobond; montare / legare PSU (transformator) pe ansamblu.",
  },
  {
    id: "supply_cable_5m_220v",
    order: 5,
    labelRo: "Atasare cablu 5 m alimentare 220V",
    meaningRo: "Cablu alimentare 5 m pentru racord 220V — material + prindere pe ansamblu.",
  },
  {
    id: "light_test",
    order: 6,
    labelRo: "Test lumină",
    meaningRo: "Verificare iluminare înainte de prinderea corpului plexi+volum pe Forex.",
  },
  {
    id: "attach_body_to_forex_on_bond",
    order: 7,
    labelRo: "Prindere corp (plexi + volum) pe Forex",
    meaningRo:
      "Față plexi + volum pe spatele Forex deja pe bond, cu autoforante fine vopsite la culoarea cantului / volumului.",
  },
  {
    id: "pack_composite",
    order: 8,
    labelRo: "Impachetare ansamblu Litere + Alucobond",
    meaningRo:
      "Un singur pack la finalul composition — nu pack ACM separat înainte de montaj litere.",
  },
];
