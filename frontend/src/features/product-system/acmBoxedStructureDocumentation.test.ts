import { describe, expect, it } from "vitest";
import { CNC_ACM_BOXED_SERVICES_RO } from "@/lib/cnc/cncProcessTaxonomyRo";
import {
  ACM_BOXED_CNC_SERVICES_RO,
  ACM_BOXED_PRINCIPAL_TASK_CHAIN,
  ACM_BOXED_STEP_DOCS,
  ACM_BOXED_STRUCTURE_TEACHING_CARDS,
  getAcmBoxedStepDoc,
  listAcmObtainTasks,
} from "./acmBoxedStructureDocumentation";
import {
  ACM_STRUCTURE_STEP_CORP_CASETAT,
  ACM_STRUCTURE_STEP_STRUCTURA_METALICA,
  canonicalizeAcmBoxedStructureStepId,
  resolveAcmBoxedStructureDetailPath,
} from "./acmBoxedStructureDetailRoutes";
import {
  ACM_BOXED_MOUNTING_TEMPLATE_CODE,
  ACM_BOXED_OWNER_LABEL_RO,
} from "./acmBoxedTemplateIdentity";

describe("acmBoxedStructureDocumentation", () => {
  it("locks owner nucleus to Corp casetat + Structură metalică", () => {
    expect(Object.keys(ACM_BOXED_STEP_DOCS)).toEqual([
      ACM_STRUCTURE_STEP_CORP_CASETAT,
      ACM_STRUCTURE_STEP_STRUCTURA_METALICA,
    ]);
    expect(ACM_BOXED_STRUCTURE_TEACHING_CARDS.map((card) => card.displayName)).toEqual([
      "Corp casetat",
      "Structură metalică",
    ]);
    expect(ACM_BOXED_OWNER_LABEL_RO).toBe("Alucobond casetat");
    // Letters-style teaser: material first, not process verbs
    expect(ACM_BOXED_STRUCTURE_TEACHING_CARDS[0]!.teaserRo).toMatch(/Alucobond casetat|L1\/L2|material desfășurat/i);
    expect(ACM_BOXED_STRUCTURE_TEACHING_CARDS[0]!.teaserRo).not.toMatch(/Decupare|V-groove|pliere|Canal/i);
    expect(ACM_BOXED_STRUCTURE_TEACHING_CARDS[1]!.teaserRo).toMatch(/Al \/ oțel|P|cutlist/i);
  });

  it("uses Decupare + V-groove for ACM (not Canal/Șanfren)", () => {
    expect([...ACM_BOXED_CNC_SERVICES_RO]).toEqual([...CNC_ACM_BOXED_SERVICES_RO]);
    expect([...ACM_BOXED_CNC_SERVICES_RO]).toEqual(["Decupare", "V-groove"]);
  });

  it("documents corp graphic process and oversized; cut is blank-based EUR/ml never time-based", () => {
    const corp = getAcmBoxedStepDoc(ACM_STRUCTURE_STEP_CORP_CASETAT);
    expect(corp.roleRo).toMatch(/pliere|aceeași placă|o singură componentă|finisaj/i);
    expect(corp.sections.some((section) => section.id === "oversized")).toBe(true);
    const cut = corp.calcCards.find((card) => card.id === "cut");
    const vg = corp.calcCards.find((card) => card.id === "vgroove-fold");
    expect(cut?.titleRo).toMatch(/Decupare/i);
    expect(vg?.titleRo).toMatch(/V-groove/i);
    expect(cut?.formulaRo).toMatch(/material desfășurat|BW\/BH/i);
    expect(cut?.formulaRo).toMatch(/1\.5 EUR\/ml|EUR\/ml/i);
    expect(cut?.formulaRo).toMatch(/NICIODATĂ pe oră \/ pe timp|pe timp/i);
    expect(cut?.notThisRo?.join(" ")).toMatch(/V-groove|Canal|Șanfren|doar.*feței/i);
    expect(vg?.formulaRo).toMatch(/3\.0 EUR\/ml|EUR\/ml/i);
    expect(vg?.stepsRo?.join(" ")).toMatch(/0\.8|90°|135°|îndoire|șanț/i);
    expect(vg?.notThisRo?.join(" ")).toMatch(/Decupare|Canal|Șanfren|pe timp/i);
    expect(listAcmObtainTasks(ACM_STRUCTURE_STEP_CORP_CASETAT).map((task) => task.id)).toEqual([
      "prep_artcam",
      "v_groove",
      "cut_exterior",
      "deburr_fold",
      "apply_foil",
      "pack_product",
    ]);
  });

  it("locks one-plate bond body: face + laterals + folds, never glued extras", () => {
    const corp = getAcmBoxedStepDoc(ACM_STRUCTURE_STEP_CORP_CASETAT);
    const onePlate = corp.sections.find((section) => section.id === "one-plate");
    expect(onePlate).toBeTruthy();
    expect(onePlate?.bodyRo).toMatch(/aceeași placă|aceeași componentă/i);
    expect(onePlate?.bulletsRo?.join(" ")).toMatch(/Niciodată lipire/i);
    expect(onePlate?.bulletsRo?.join(" ")).toMatch(/Fold count/i);
    expect(corp.sections.find((s) => s.id === "boundary")?.bulletsRo?.join(" ")).toMatch(
      /lipit|alt material/i,
    );
  });

  it("documents metal frame Al/steel interior fasten from OWNER_RULES", () => {
    const frame = getAcmBoxedStepDoc(ACM_STRUCTURE_STEP_STRUCTURA_METALICA);
    expect(frame.heroCodeRo).toMatch(/MAT-STRUCT-ALUMINIUM/);
    expect(frame.roleRo).toMatch(/interior/i);
    expect(frame.calcCards.some((card) => /panel − 2×t − 2|2×t − 2/i.test(card.formulaRo))).toBe(
      true,
    );
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN.map((task) => task.id)).toContain("frame_make");
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN.map((task) => task.id)).toContain("frame_fasten");
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN.map((task) => task.id)).not.toContain("install_led");
  });

  it("locks owner workshop chain ArtCAM → V → cut → fold → frame → foil XOR paint → pack", () => {
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN.map((task) => task.id)).toEqual([
      "prep_artcam",
      "v_groove",
      "cut_exterior",
      "deburr_fold",
      "frame_make",
      "frame_fasten",
      "apply_foil",
      "paint_screws_if_no_foil",
      "prep_mounting_accessories",
      "pack_product",
    ]);
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN.find((t) => t.id === "apply_foil")?.conditionRo).toMatch(
      /selectat/i,
    );
    expect(
      ACM_BOXED_PRINCIPAL_TASK_CHAIN.find((t) => t.id === "paint_screws_if_no_foil")?.conditionRo,
    ).toMatch(/NU este selectat/i);
  });

  it("locks cutlist symbol P as owner-confirmed variable (SKU still deferred)", () => {
    const frame = getAcmBoxedStepDoc(ACM_STRUCTURE_STEP_STRUCTURA_METALICA);
    const cutlist = frame.sections.find((section) => section.id === "cutlist");
    expect(cutlist?.bodyRo).toMatch(/OWNER_CONFIRMED.*variabilă|variabilă.*OWNER_CONFIRMED/i);
    expect(cutlist?.bulletsRo?.join(" ")).toMatch(/P = latura exterioară|P = lățime/i);
    expect(frame.calcCards.some((card) => card.id === "cutlist-p")).toBe(true);
    expect(JSON.stringify(frame.calcCards)).toMatch(/2×P/);
  });

  it("teaches ACM finishes on Corp and colant-after-fasten on Frame (MIXED §5/7/8)", () => {
    const corp = getAcmBoxedStepDoc(ACM_STRUCTURE_STEP_CORP_CASETAT);
    expect(corp.sections.map((s) => s.id)).toEqual(
      expect.arrayContaining(["finish-zones", "finish-types", "foil-strategy"]),
    );
    expect(corp.sections.find((s) => s.id === "finish-types")?.bulletsRo?.join(" ")).toMatch(
      /Oracal 651|Print \+ laminare|Culoare placă/i,
    );
    expect(corp.calcCards.some((card) => card.id === "finish-foil")).toBe(true);
    expect(listAcmObtainTasks(ACM_STRUCTURE_STEP_CORP_CASETAT).map((t) => t.id)).toEqual(
      expect.arrayContaining(["apply_foil", "prep_artcam", "deburr_fold"]),
    );

    const frame = getAcmBoxedStepDoc(ACM_STRUCTURE_STEP_STRUCTURA_METALICA);
    const fasten = frame.sections.find((s) => s.id === "fasten");
    expect(fasten?.titleRo).toMatch(/colant/i);
    expect(fasten?.bulletsRo?.join(" ")).toMatch(/XOR|colant|vopsire/i);
    expect(frame.calcCards.some((card) => card.id === "colant-order")).toBe(true);
    expect(ACM_BOXED_PRINCIPAL_TASK_CHAIN.map((t) => t.id)).toContain("paint_screws_if_no_foil");
  });

  it("maps seed BOM comps and legacy steps into Corp casetat", () => {
    expect(
      resolveAcmBoxedStructureDetailPath(ACM_BOXED_MOUNTING_TEMPLATE_CODE, {
        type: "STRUCTURA",
        component_id: "comp_acm_panel_face",
        name: "face",
      }),
    ).toContain("/structure/corp-casetat");
    expect(
      resolveAcmBoxedStructureDetailPath(ACM_BOXED_MOUNTING_TEMPLATE_CODE, {
        type: "TAIERE_CNC_LASER",
        component_id: "comp_casetted_returns",
        name: "returns",
      }),
    ).toContain("/structure/corp-casetat");
    expect(canonicalizeAcmBoxedStructureStepId("fata-panou")).toBe(ACM_STRUCTURE_STEP_CORP_CASETAT);
    expect(canonicalizeAcmBoxedStructureStepId("casetare")).toBe(ACM_STRUCTURE_STEP_CORP_CASETAT);
    expect(canonicalizeAcmBoxedStructureStepId("prinderi-asamblare")).toBe(
      ACM_STRUCTURE_STEP_CORP_CASETAT,
    );
  });
});
