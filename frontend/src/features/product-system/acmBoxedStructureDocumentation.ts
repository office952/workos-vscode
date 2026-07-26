/**
 * Alucobond casetat — Product System structure documentation (display SoT).
 *
 * Owner nucleus (2026-07-23): Corp casetat + Structură metalică.
 * Process / frame / oversized authority = MIXED + ACP_INTERNAL_FRAME_OWNER_RULES
 * (not the seed 3-component BOM slice as co-equal cards).
 */
import { CNC_ACM_BOXED_SERVICES_RO } from "@/lib/cnc/cncProcessTaxonomyRo";
import {
  ACM_BOXED_PRINCIPAL_TASK_CHAIN,
  type AcmBoxedPrincipalTask,
} from "./acmBoxedStructurePrincipalTaskOrder";
import {
  ACM_BOXED_FAMILY_LABEL_RO,
  ACM_BOXED_MATERIAL_PANEL_CODE,
  ACM_BOXED_MATERIAL_PANEL_LABEL_RO,
  ACM_BOXED_MOUNTING_TEMPLATE_CODE,
  ACM_BOXED_OWNER_LABEL_RO,
} from "./acmBoxedTemplateIdentity";
import type { AcmBoxedStructureStepId } from "./acmBoxedStructureDetailRoutes";
import {
  ACM_STRUCTURE_STEP_CORP_CASETAT,
  ACM_STRUCTURE_STEP_STRUCTURA_METALICA,
} from "./acmBoxedStructureDetailRoutes";

export {
  ACM_BOXED_PRINCIPAL_TASK_CHAIN,
  type AcmBoxedPrincipalTask,
  type AcmBoxedPrincipalTaskId,
} from "./acmBoxedStructurePrincipalTaskOrder";

export type AcmBoxedDocSection = {
  id: string;
  titleRo: string;
  bodyRo: string;
  bulletsRo?: readonly string[];
};

export type AcmBoxedCalcCard = {
  id: string;
  importance: 1 | 2;
  titleRo: string;
  subtitleRo: string;
  formulaRo: string;
  stepsRo: readonly string[];
  outputsRo: readonly string[];
  notThisRo: readonly string[];
  priceNoteRo: string;
  verifyHref: string;
  verifyLabelRo: string;
};

export type AcmBoxedStepDoc = {
  stepId: AcmBoxedStructureStepId;
  stepIndex: 1 | 2;
  titleRo: string;
  heroMaterialRo: string;
  heroCodeRo: string;
  roleRo: string;
  obtainTitleRo: string;
  withoutTheseRo: string;
  obtainTaskIds: readonly string[];
  sections: readonly AcmBoxedDocSection[];
  calcCards: readonly AcmBoxedCalcCard[];
};

export const ACM_BOXED_CARD_NOT_TASK_HELPER_RO =
  "Ordinea taskurilor e pe fiecare pagină de componentă — card ≠ task.";

export const ACM_BOXED_STRUCTURE_HELPER_RO =
  "Corp casetat · Structură metalică → pagină detaliu. Fără litere/LED litere în nucleu.";

export const ACM_BOXED_CORP_STRUCTURE_DISPLAY_NAME = "Corp casetat";
export const ACM_BOXED_FRAME_STRUCTURE_DISPLAY_NAME = "Structură metalică";

export const ACM_BOXED_CORP_STRUCTURE_TYPE_LABEL = "Corp casetat";
export const ACM_BOXED_FRAME_STRUCTURE_TYPE_LABEL = "Structură metalică";

/**
 * ACM/Dibond casetat CNC: Decupare + V-groove (owner taxonomy elements 1 + 3).
 * Canal/Șanfren = litere only — do not alias V-groove to Canal/Șanfren.
 */
export const ACM_BOXED_CNC_SERVICES_RO = CNC_ACM_BOXED_SERVICES_RO;

/**
 * Structure cards follow Letters teaser pattern: material first · short hints.
 * Process (Decupare / V-groove / pliere / cutlist) lives on the detail page.
 */
export const ACM_BOXED_STRUCTURE_TEACHING_CARDS = [
  {
    stepId: ACM_STRUCTURE_STEP_CORP_CASETAT,
    typeLabel: ACM_BOXED_CORP_STRUCTURE_TYPE_LABEL,
    displayName: ACM_BOXED_CORP_STRUCTURE_DISPLAY_NAME,
    /** Letters-style: material · key sizes · unit hint */
    teaserRo: `${ACM_BOXED_OWNER_LABEL_RO} · L1/L2 · material desfășurat`,
    teaserHintRo: "· finisaj față/volum",
  },
  {
    stepId: ACM_STRUCTURE_STEP_STRUCTURA_METALICA,
    typeLabel: ACM_BOXED_FRAME_STRUCTURE_TYPE_LABEL,
    displayName: ACM_BOXED_FRAME_STRUCTURE_DISPLAY_NAME,
    teaserRo: "Cadru Al / oțel · P · cutlist",
    teaserHintRo: "· colant după fixare",
  },
] as const;

export const ACM_BOXED_DOC_SOURCES = [
  {
    labelRo: "Ordine taskuri atelier casetare bond (owner 10 pași)",
    path: "frontend/src/features/product-system/acmBoxedStructurePrincipalTaskOrder.ts",
  },
  {
    labelRo: "Audit ordine taskuri casetare bond",
    path: "docs/worklog/realignment/audit__acm_casetare_bond_task_order_v1.md",
  },
  {
    labelRo: "Taxonomie CNC RO + schițe (Decupare · Canal/Șanfren · V-groove)",
    path: "docs/architecture/CNC_PROCESS_TAXONOMY_RO.md",
  },
  {
    labelRo: "MIXED — Corp CNC §4 · fixare/colant §5 · finisaj §7 · folie §8 · oversized §11",
    path: "docs/architecture/MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md",
  },
  {
    labelRo: "Reguli cadru interior (OWNER_CONFIRMED) + simbol P",
    path: "docs/decisions/ACP_INTERNAL_FRAME_OWNER_RULES.md",
  },
  {
    labelRo: "Catalog Oracal / vinyl partajat",
    path: "docs/architecture/SHARED_VINYL_MATERIAL_CATALOG.md",
  },
  {
    labelRo: "Nesting / oversized foaie · lățimi Oracal",
    path: "docs/architecture/product-system/MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md",
  },
  {
    labelRo: "Material desfășurat W/H · L1/L2 · +10 mm CNC",
    path: "docs/architecture/ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md",
  },
  {
    labelRo: "Schiță V-groove → pliu (geometrie owner)",
    path: "docs/worklog/realignment/audit_assets/24_acm_vgroove_fold_geometry.png",
  },
  {
    labelRo: "DXF ArtCAM owner — un pliu + două pliuri (Cut outside / V-groove along line)",
    path: "docs/architecture/ACM_ARTCAM_DXF_OWNER_GOLDEN.md",
  },
  {
    labelRo: "DXF un pliu 200×30 cm",
    path: "docs/worklog/realignment/audit_assets/30_acm_un_pliu_200x30_owner.dxf",
  },
  {
    labelRo: "DXF două pliuri L1=10 cm L2=3 cm",
    path: "docs/worklog/realignment/audit_assets/30_acm_2_pliuri_100x30_owner.dxf",
  },
  {
    labelRo: "Seed live (ops BOM slice — nu nucleu UI)",
    path: "backend/seeds/seed_tpl_acm_boxed_mounting_support_v1.py",
  },
  {
    labelRo: "Amendament UI Corp + Frame + finisaje",
    path: "docs/worklog/realignment/2026-07-23_acm_ps_structure_corp_frame_ui_v2.md",
  },
] as const;

export const ACM_BOXED_STEP_DOCS: Record<AcmBoxedStructureStepId, AcmBoxedStepDoc> = {
  [ACM_STRUCTURE_STEP_CORP_CASETAT]: {
    stepId: ACM_STRUCTURE_STEP_CORP_CASETAT,
    stepIndex: 1,
    titleRo: ACM_BOXED_CORP_STRUCTURE_DISPLAY_NAME,
    heroMaterialRo: ACM_BOXED_MATERIAL_PANEL_LABEL_RO,
    heroCodeRo: ACM_BOXED_MATERIAL_PANEL_CODE,
    roleRo: `Pasul 1 din Structură ${ACM_BOXED_OWNER_LABEL_RO}: o singură componentă — corpul din bond (V + debitare + pliere) plus finisaje față/volum (MIXED §7–8). Față + laterale + ultimele pliuri = aceeași placă. Colantul se aplică după fixarea cadrului (pasul 2).`,
    obtainTitleRo: "Cum obții Corp casetat",
    withoutTheseRo:
      "Fără pregătire ArtCAM, V-groove, debitare contur și formare casetă nu există corpul; finisajul se aplică după cadru (sau vopsire șuruburi fără colant).",
    obtainTaskIds: [
      "prep_artcam",
      "v_groove",
      "cut_exterior",
      "deburr_fold",
      "apply_foil",
      "pack_product",
    ],
    sections: [
      {
        id: "role",
        titleRo: "Ce este Corp casetat",
        bodyRo: `${ACM_BOXED_OWNER_LABEL_RO} — o componentă: carcasa din bond (${ACM_BOXED_FAMILY_LABEL_RO}). Cod template ${ACM_BOXED_MOUNTING_TEMPLATE_CODE}.`,
        bulletsRo: [
          "Nucleu pas 1/2 — înainte de structura metalică",
          "Material corp: doar ACM/ACP/Dibond/Alucobond (alias magazin)",
          "Seed face/returns/assembly = linii ops/BOM pe aceeași componentă — nu corpuri separate",
          "Nu confunda cu MAT-ACP-FATA-LITERE (plexi litere)",
        ],
      },
      {
        id: "one-plate",
        titleRo: "O placă · un corp (owner)",
        bodyRo: "Indiferent câte folduri are: fața, lateralele și ultimele pliuri sunt din bond pe aceeași componentă. Când nu e segmentat (mai multe panouri din cauza foii), corpul e din aceeași placă — gravată și îndoită.",
        bulletsRo: [
          "Niciodată alt material ca „corp diferit” (nu plexi, nu Forex, nu profil Al pe lateralele corpului)",
          "Niciodată lipire de elemente extra ca să formezi corpul casetat",
          "Fold count (1 / 2 / …) nu schimbă materialul și nu creează componente corp noi",
          "Segmentarea (MIXED §11) = mai multe panouri-corp din bond, fiecare tot mono-placă; nu lipire pe laterale",
        ],
      },
      {
        id: "process",
        titleRo: "Ordine atelier casetare bond (owner)",
        bodyRo:
          "SoT: acmBoxedStructurePrincipalTaskOrder — ArtCAM → V-groove → debitare contur → debavurare+pliere → cadru → prindere → colant SAU vopsire șuruburi → accesorii montaj → pack.",
        bulletsRo: [
          "1 Pregătire ArtCAM (cote, desfășurată, linii V, contur, toleranțe)",
          "2 Frezare V-groove / linii de îndoire",
          "3 Debitare finală contur exterior (Cut outside)",
          "4 Curățare muchii / debavurare + îndoiri / formare casetă",
          "Apoi cadru · prindere · finisaj după fixare (colant) sau vopsire autoforante fără colant",
        ],
      },
      {
        id: "finish-zones",
        titleRo: "Finisaj față ≠ finisaj volum (MIXED §7)",
        bodyRo: "Zone distincte pe același corp bond. Fiecare zonă se alege independent; combinațiile sunt valide.",
        bulletsRo: [
          "Față = planul vizibil al casetei",
          "Volum = lateralele / returns (primul pliu și, dacă e cazul, L2)",
          "Exemple OK: față Oracal + volum placă; față print+lam + volum Oracal; ambele la fel; ambele diferite",
          "Runtime Finish Contract pe shell: Intake AcmPanel → Material și finisaj (shell_finish v1); CostEngine încă gap",
        ],
      },
      {
        id: "finish-types",
        titleRo: "Tipuri permise pe zonă (MIXED §7)",
        bodyRo: "Doar aceste trei tipuri pe shell ACM casetat — nu inventa catalog nou.",
        bulletsRo: [
          "Culoare placă (stock — fără vinyl)",
          "Oracal 651 — MAT-ORACAL-651 / ORACAL_651 / culori 651-xxx",
          "Print + laminare (exterior): Print → Laminare → Aplicare",
          "Nu pe ACM shell: Oracal 641/8500, RAL cant litere, finisaj plexi litere",
          "Face treatment (decupaj / insert) ≠ finisaj folie — construcție separată",
        ],
      },
      {
        id: "foil-strategy",
        titleRo: "Strategie folie (MIXED §8)",
        bodyRo: "Lățimi din catalog (nu inventate). Preferință owner, apoi client informat la îmbinări.",
        bulletsRo: [
          "1) Față + primul pliu dintr-o bucată (dacă latimea permite)",
          "2) Față o bucată; volum separat (N/S/E/W)",
          "3) Față multi-bucăți; îmbinări discrete; suprapunere mică; client informat",
          "Oracal util ~960 / 1220 (role 1000 / 1260); print+lam UI 1050 / 1320 / 1500",
          "De salvat (Finish Contract): material · latime · orientare · față+primul pliu · nr bucăți · îmbinări · client informat",
        ],
      },
      {
        id: "oversized",
        titleRo: "Panou mai mare decât foaia (MIXED §11)",
        bodyRo: "Produsul vizual = un ansamblu; fizic = mai multe panouri-corp (tot din bond) unite la montaj — nu „piese lipite” ca un corp mono.",
        bulletsRo: [
          "Sistemul nu împarte automat — propune confirmare",
          "Fiecare panou-corp rămâne placă gravată + îndoită",
          "Nesting: oversized_for_sheet → split/panelization cu confirmare operator",
          "Foaie ACM tipică pick: 3000×1500, overflow 4000×1500",
        ],
      },
      {
        id: "boundary",
        titleRo: "Ce nu este aici",
        bodyRo: "Corp ACM din bond — fără litere plexi/cant/Forex/LED litere; fără cadru metalic (pasul 2); fără laterale din alt material.",
        bulletsRo: [
          "Nu = Vizual față litere / cant Al litere / RAL cant",
          "Nu = Structură metalică / acp_internal_frame",
          "Nu = corp lipit din „față + returns” ca piese separate",
          "Nu = Composer Litere↔ACM (încă)",
        ],
      },
    ],
    calcCards: [
      {
        id: "cut",
        importance: 1,
        titleRo: "Decupare CNC",
        subtitleRo: "Element CNC #1 · CUT_ACM_PANEL",
        formulaRo:
          "material desfășurat · qty Decupare ≈ 2×(BW+BH)/1000 ml × 1.5 EUR/ml · BW/BH = W/H + 2×(L1[+L2]) + 10 — NICIODATĂ pe oră / pe timp; nu doar față",
        stepsRo: [
          "Confirmă față W×H + L1[+L2] → material desfășurat",
          "Decupare: freza taie placa pe contur (prin material)",
          "Cantitate comercială = perimetru material desfășurat (ml) — nu timp CNC",
        ],
        outputsRo: ["Contur decupat", "Linie CPP acm_panel_cut"],
        notThisRo: [
          "Nu = V-groove (îndoire Dibond)",
          "Nu = Canal / Șanfren litere",
          "Nu = doar dimensiunea feței (proxy legacy retras)",
          "Nu = tarif pe oră / pe timp",
        ],
        priceNoteRo: "Owner-locked 2026-07-23: pe material desfășurat · 1.5 EUR/ml (repo: blank_*)",
        verifyHref: "/inventory/pricing",
        verifyLabelRo: "Pricing Registry",
      },
      {
        id: "vgroove-fold",
        importance: 1,
        titleRo: "V-groove CNC + pliere atelier",
        subtitleRo: "Element CNC #3 · doar Dibond/ACM îndoire · apoi FOLD",
        formulaRo:
          "comercial V-groove: fold_length_m × 3.0 EUR/ml (ACM_V_GROOVE) — NICIODATĂ pe oră / pe timp · pliere: manoperă FOLD (adesea neprețuit quote)",
        stepsRo: [
          "V-groove CNC: șanț V pe linia de pliu (partea opusă feței) — piele ~0.8 mm; special pentru îndoire",
          "Casetă tipică: 90° / bază 3 mm → pliu 90° (alt caz: 135° / 2 mm → 45°)",
          "Cantitate comercială = fold_length_m (ml) — nu minute freză",
          "Pliere atelier după CNC: formare laterale + ultime pliuri pe șanțurile V",
        ],
        outputsRo: ["Șanțuri V pe material desfășurat", "Corp casetat după pliere", "Linie CPP acm_v_groove"],
        notThisRo: [
          "Nu = Decupare (V nu străpunge)",
          "Nu = Canal / Șanfren litere (alt scop: lipire volum pe față)",
          "Nu = tarif pe oră / pe timp",
          "Nu = cadru metalic",
        ],
        priceNoteRo: "Owner-confirmed 3 EUR/ml; geometrie: audit_assets/24_acm_vgroove_fold_geometry.png",
        verifyHref: "/inventory/pricing",
        verifyLabelRo: "Pricing Registry",
      },
      {
        id: "blank-oversized",
        importance: 2,
        titleRo: "Material desfășurat + oversized",
        subtitleRo: "W/H · L1/L2 · +10 mm CNC",
        formulaRo: "BW/BH = W/H + 2×(L1[+L2]) + 10 mm (cnc_fixing_margin) · oversized → segmentare confirmată",
        stepsRo: [
          "Față = W×H; volum/retrageri = din fold_count + L1 (+ L2)",
          "Material desfășurat = față + (L1×2) + (L2×2 dacă fold_count=2) + 10 mm marjă fixare CNC",
          "Compară materialul desfășurat cu foaia; dacă nu încape: fundal segmentat (confirmare)",
        ],
        outputsRo: ["dimensiuni material desfășurat (repo: blank_width_mm / blank_height_mm)", "sau plan multi-panou"],
        notThisRo: ["Nu inventa split fără operator", "Nu trata panourile ca SKU separate"],
        priceNoteRo: "Nesting / segmentare — Intake + MIXED §11; blankPreviewMm",
        verifyHref: "/intake-v6/operator",
        verifyLabelRo: "Intake V6",
      },
      {
        id: "finish-foil",
        importance: 1,
        titleRo: "Finisaj + folie",
        subtitleRo: "MIXED §7–8 · teaching",
        formulaRo: "zonă ∈ {față, volum} × tip ∈ {placă, Oracal 651, print+lam} · strategie folie 1→2→3",
        stepsRo: [
          "Alege tip pe față și pe volum (independente)",
          "Dacă e vinyl/print: alege strategie (față+primul pliu / volum separat / multi-bucăți)",
          "Aplicarea colantului = după fixarea cadrului (pasul Structură metalică)",
        ],
        outputsRo: ["Decizie finisaj față", "Decizie finisaj volum", "Strategie folie + mesaj client dacă e cazul"],
        notThisRo: [
          "Nu = finisaj litere (641/8500/RAL cant)",
          "Nu aplica colant înainte de șuruburi când e colant",
          "Nu inventa lățimi folie în afara catalogului",
        ],
        priceNoteRo: "Prețuri vinyl/print în Pricing Registry — nu pe această pagină",
        verifyHref: "/inventory/pricing",
        verifyLabelRo: "Pricing Registry",
      },
    ],
  },
  [ACM_STRUCTURE_STEP_STRUCTURA_METALICA]: {
    stepId: ACM_STRUCTURE_STEP_STRUCTURA_METALICA,
    stepIndex: 2,
    titleRo: ACM_BOXED_FRAME_STRUCTURE_DISPLAY_NAME,
    heroMaterialRo: "Cadru aluminiu sau oțel (interior)",
    heroCodeRo: "MAT-STRUCT-ALUMINIUM · MAT-STRUCT-STEEL",
    roleRo: `Pasul 2 din Structură ${ACM_BOXED_OWNER_LABEL_RO}: cadru metalic confectionat în atelier, prins pe interiorul corpului Alucobond. După fixare — colant (dacă finisajul Corp e vinyl/print). Nu e premontaj Litere; nu e CNC pe foaia ACM.`,
    obtainTitleRo: "Cum obții Structură metalică",
    withoutTheseRo:
      "Fără confecționare cadru, prindere pe corp și (colant SAU vopsire șuruburi) produsul nu e gata de montaj/pack.",
    obtainTaskIds: [
      "frame_make",
      "frame_fasten",
      "apply_foil",
      "paint_screws_if_no_foil",
      "prep_mounting_accessories",
      "pack_product",
    ],
    sections: [
      {
        id: "role",
        titleRo: "Ce este Structura metalică",
        bodyRo: "Cadru interior ACP/ACM (`acp_internal_frame`) — atelier, nu CNC pe panou.",
        bulletsRo: [
          "Material: aluminiu sau oțel — ambele OWNER_CONFIRMED",
          "Prindere: pe interiorul Alucobondului (autoforante cap înecat)",
          "≠ TPL-METAL-PREMOUNT-STRUCTURE_v1 (premontaj litere)",
          "Profiluri SKU: DEFERRED — nu hardcoda 20×20×1.5 ca default",
        ],
      },
      {
        id: "formula",
        titleRo: "Formulă cadru (OWNER_CONFIRMED)",
        bodyRo: "frame_outer = panel_outer − 2×grosime_panou − 2 mm (luft total fix).",
        bulletsRo: [
          "Exemplu: panou 2000×700×3 → cadru 1992×692",
          "Identic single fold = double fold (fold count nu schimbă cota)",
          "Nu folosi vechiul clearance 5 mm ca authority",
        ],
      },
      {
        id: "cutlist",
        titleRo: "Confectionare / cutlist (MIXED §6)",
        bodyRo: "Salvat: dimensiune, material, orientare, lungi/scurte, traverse, listă debitare. Simbol P = lățimea exterioară a profilului (mm) — OWNER_CONFIRMED ca variabilă; valoarea SKU încă DEFERRED.",
        bulletsRo: [
          "P = latura exterioară profil (mm): 20×20 → P=20; 30×30 → P=30",
          "1.5 mm (ex. 20×20×1.5) = grosime perete în carne — nu e P; nu intră în −2×P",
          "Lungi = cotă cadru completă → 2 piese",
          "Scurte = cotă − 2×P → 2 piese",
          "Traverse = lungime ca scurte → N piese (sugestie spacing; operator confirmă)",
          "SKU / default pentru P: încă DEFERRED",
        ],
      },
      {
        id: "fasten",
        titleRo: "Fixare pe interior + colant (MIXED §5)",
        bodyRo: "Contur; autoforante cap înecat; fără pas/dimensiune inventate. Ordinea față de finisajul Corp e obligatorie.",
        bulletsRo: [
          "Cu autocolant: prindere cadru → aplicare autocolant (capete acoperite) — NU vopsi șuruburi",
          "Fără autocolant: prindere cadru → vopsire autoforante la culoarea Alucobondului",
          "XOR: pasul 7 (colant) și pasul 8 (vopsire șuruburi) — nu ambele",
          "Apoi accesorii montaj + impachetare",
          "Runtime Aggregate/CPP: BOM cadru încă incomplet — docs = truth teaching",
        ],
      },
    ],
    calcCards: [
      {
        id: "frame-size",
        importance: 1,
        titleRo: "Cotă cadru",
        subtitleRo: "panel − 2×t − 2 mm",
        formulaRo: "W_f = W_p − 2×t − 2 · H_f = H_p − 2×t − 2",
        stepsRo: [
          "Ia dimensiunea exterioară panou + grosime material",
          "Aplică formula OWNER_CONFIRMED",
          "Nu modifica cota după nr. de pliuri",
        ],
        outputsRo: ["frame_outer_width_mm", "frame_outer_height_mm"],
        notThisRo: ["Nu = clearance min/max editabil", "Nu = premount letters"],
        priceNoteRo: "Fără preț inventat pe PS — registry / GO ulterior",
        verifyHref: "/product-system/products",
        verifyLabelRo: "Product System",
      },
      {
        id: "cutlist-p",
        importance: 1,
        titleRo: "Cutlist cu P",
        subtitleRo: "P = lățime profil (OWNER_CONFIRMED)",
        formulaRo: "2×lungi(cotă) + 2×scurte(cotă−2×P) + N×traverse(cotă−2×P)",
        stepsRo: [
          "Calculează W_f × H_f (cadru)",
          "Alege material; P vine din profilul ales (SKU încă DEFERRED ca default)",
          "Sugerează N traverse (oțel 1000 / Al 750); operator confirmă",
        ],
        outputsRo: ["Listă debitare: lungi, scurte, traverse"],
        notThisRo: [
          "Nu inventa P fără profil confirmat pe comandă",
          "Nu = calcul structural certificat",
          "Nu aproba 20×20 ca default doar din exemplul didactic",
        ],
        priceNoteRo: "Display teaching — Aggregate frame BOM still gap",
        verifyHref: "/intake-v6/operator",
        verifyLabelRo: "Intake V6",
      },
      {
        id: "colant-order",
        importance: 1,
        titleRo: "Ordine colant",
        subtitleRo: "MIXED §5",
        formulaRo: "cadru + șuruburi → (colant DACĂ selectat) XOR (vopsire autoforante DACĂ fără colant)",
        stepsRo: [
          "Montează cadrul pe interiorul corpului casetat",
          "Dacă autocolant selectat: aplică după fixare (pas 7)",
          "Dacă fără autocolant: vopsește autoforantele la culoarea Alucobond (pas 8)",
        ],
        outputsRo: ["Corp finisat sau șuruburi vopsite", "Apoi accesorii montaj + pack"],
        notThisRo: [
          "Nu colanta înainte de fixare",
          "Nu vopsi capetele dacă urmează / există colant",
          "Nu aplica ambele 7 și 8",
        ],
        priceNoteRo: "Manoperă / material vinyl — Pricing Registry",
        verifyHref: "/inventory/pricing",
        verifyLabelRo: "Pricing Registry",
      },
    ],
  },
};

export function getAcmBoxedStepDoc(stepId: AcmBoxedStructureStepId): AcmBoxedStepDoc {
  return ACM_BOXED_STEP_DOCS[stepId];
}

export function listAcmObtainTasks(stepId: AcmBoxedStructureStepId): AcmBoxedPrincipalTask[] {
  const doc = getAcmBoxedStepDoc(stepId);
  const byId = new Map(ACM_BOXED_PRINCIPAL_TASK_CHAIN.map((task) => [task.id, task]));
  return doc.obtainTaskIds
    .map((id) => byId.get(id))
    .filter((task): task is AcmBoxedPrincipalTask => task != null);
}

export function isAcmTaskOwnedByStep(
  task: AcmBoxedPrincipalTask,
  stepId: AcmBoxedStructureStepId,
): boolean {
  return task.stepIds.includes(stepId);
}
