/**
 * Principal workshop task order — Alucobond / Dibond casetat.
 * Display SoT on Product System Structure pages. Not ExecutionPlan authority.
 *
 * OWNER_CONFIRMED 2026-07-23 (atelier sequence).
 * Mirror: docs/worklog/realignment/audit__acm_casetare_bond_task_order_v1.md
 */

import type { AcmBoxedStructureStepId } from "./acmBoxedStructureDetailRoutes";
import {
  ACM_STRUCTURE_STEP_CORP_CASETAT,
  ACM_STRUCTURE_STEP_STRUCTURA_METALICA,
} from "./acmBoxedStructureDetailRoutes";

export type AcmBoxedPrincipalTaskId =
  | "prep_artcam"
  | "v_groove"
  | "cut_exterior"
  | "deburr_fold"
  | "frame_make"
  | "frame_fasten"
  | "apply_foil"
  | "paint_screws_if_no_foil"
  | "prep_mounting_accessories"
  | "pack_product";

export type AcmBoxedPrincipalTask = {
  id: AcmBoxedPrincipalTaskId;
  order: number;
  labelRo: string;
  meaningRo: string;
  stepIds: readonly AcmBoxedStructureStepId[];
  conditionRo?: string;
};

/**
 * Full workshop chain — casetare bond + cadru + finisaj după fixare + pack.
 * Owner numbering: 1–9 then pack as 10 (second „8” in owner note = pack).
 */
export const ACM_BOXED_PRINCIPAL_TASK_CHAIN: readonly AcmBoxedPrincipalTask[] = [
  {
    id: "prep_artcam",
    order: 1,
    labelRo: "Pregătire fișier ArtCAM",
    meaningRo:
      "Cote finale · material desfășurat (blank intern) · linii V-groove · contur exterior · toleranțe. Grafica CNC înainte de mașină.",
    stepIds: [ACM_STRUCTURE_STEP_CORP_CASETAT],
  },
  {
    id: "v_groove",
    order: 2,
    labelRo: "Frezare V-groove / linii de îndoire pentru casetare",
    meaningRo:
      "Șanț V pe linia de pliu (piele ~0.8 mm) — ArtCAM: V-groove along line (trasee roșii). Nu e Canal/Șanfren litere.",
    stepIds: [ACM_STRUCTURE_STEP_CORP_CASETAT],
  },
  {
    id: "cut_exterior",
    order: 3,
    labelRo: "Debitare finală pe conturul exterior",
    meaningRo:
      "Decupare prin material pe contur — ArtCAM: Cut outside (exterior negru). Pe materialul desfășurat.",
    stepIds: [ACM_STRUCTURE_STEP_CORP_CASETAT],
  },
  {
    id: "deburr_fold",
    order: 4,
    labelRo: "Curățare muchii / debavurare + îndoiri laterale / formare casetă",
    meaningRo:
      "După CNC: debavurare + pliere / formare corp casetat din aceeași placă bond. Manoperă atelier.",
    stepIds: [ACM_STRUCTURE_STEP_CORP_CASETAT],
  },
  {
    id: "frame_make",
    order: 5,
    labelRo: "Confecționare cadru metalic cf. specificații",
    meaningRo:
      "Cadru Al sau oțel; cutlist cu P; formulă frame = panel − 2×grosime − 2 mm.",
    stepIds: [ACM_STRUCTURE_STEP_STRUCTURA_METALICA],
  },
  {
    id: "frame_fasten",
    order: 6,
    labelRo: "Prindere cadru metalic de corpul casetat din Alucobond",
    meaningRo:
      "Autoforante cap înecat pe interiorul corpului casetat — înainte de colant (dacă e cazul).",
    stepIds: [ACM_STRUCTURE_STEP_STRUCTURA_METALICA],
  },
  {
    id: "apply_foil",
    order: 7,
    labelRo: "Aplicare autocolant solicitat cf. specificații",
    meaningRo:
      "Oracal 651 / print+lam pe față și/sau volum — după fixarea cadrului. Folia acoperă capetele.",
    stepIds: [ACM_STRUCTURE_STEP_CORP_CASETAT, ACM_STRUCTURE_STEP_STRUCTURA_METALICA],
    conditionRo: "Când autocolant / folie este selectat pe comandă",
  },
  {
    id: "paint_screws_if_no_foil",
    order: 8,
    labelRo: "Vopsire autoforante la culoarea Alucobondului",
    meaningRo:
      "Dacă NU e solicitat autocolant: capetele șuruburilor se vopsesc la culoarea plăcii — nu rămân netratate.",
    stepIds: [ACM_STRUCTURE_STEP_STRUCTURA_METALICA],
    conditionRo: "Când autocolantul NU este selectat",
  },
  {
    id: "prep_mounting_accessories",
    order: 9,
    labelRo: "Pregătire accesorii de montaj",
    meaningRo: "Pregătește pentru montaj accesoriile de montaj cf. specificații.",
    stepIds: [ACM_STRUCTURE_STEP_STRUCTURA_METALICA],
  },
  {
    id: "pack_product",
    order: 10,
    labelRo: "Impachetare produs cf. specificații",
    meaningRo: "Impachetează produsul conform specificațiilor de livrare / comandă.",
    stepIds: [ACM_STRUCTURE_STEP_CORP_CASETAT, ACM_STRUCTURE_STEP_STRUCTURA_METALICA],
  },
] as const;
