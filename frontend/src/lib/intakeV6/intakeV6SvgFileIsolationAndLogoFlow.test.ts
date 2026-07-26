import { readFileSync } from "fs";
import { resolve } from "path";
import { describe, expect, it } from "vitest";

import { analyzeSvgString } from "@/lib/svgAnalyzer";
import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { confirmAllSuggestedLayerRoles } from "./intakeV4LayerRoleBridge";
import {
  deriveLetterGroupsFromAnalyzer,
  mergeLetterGroupFinishes,
  type IntakeV6LetterGroupFinish,
} from "./intakeV6LetterGroups";
import {
  deriveArtworkFinishesFromAnalyzer,
  mergeArtworkFinishes,
  type IntakeV6ArtworkFinish,
} from "./intakeV6ArtworkFinish";
import { resolveIntakeV6LayerTargetTemplate } from "./intakeV6LayerTargetTemplate";

const SVG_DIR = resolve(__dirname, "../../../../fisiere-teste-svg");
const REQUIRED_FILES = [
  "gradi-curat.svg",
  "litere-vol-1-layer.svg",
  "litere-vol-2-layere.svg",
  "logo.svg",
] as const;

function analyzeFixture(fileName: (typeof REQUIRED_FILES)[number]) {
  const source = readFileSync(resolve(SVG_DIR, fileName), "utf8");
  return analyzeSvgString(source, fileName, source.length).report as SvgAnalysisCoreReport;
}

function confirmAll(report: SvgAnalysisCoreReport): LayerRoleConfirmation {
  return {
    ...report.layerRoleConfirmation,
    confirmationStatus: "complete",
    layers: report.layerRoleConfirmation.layers.map((layer) => ({
      ...layer,
      confirmedRole: layer.autoRole,
      confirmationState: "confirmed",
    })),
  };
}

function layerNames(report: SvgAnalysisCoreReport): string[] {
  return report.layers.map((layer) => layer.name);
}

function targetTemplates(report: SvgAnalysisCoreReport): string[] {
  return report.layers.map((layer) => {
    const selectedRole = report.layerRoleConfirmation.layers.find(
      (entry) => entry.layerKey === layer.id || entry.layerName === layer.name,
    )?.autoRole;
    return resolveIntakeV6LayerTargetTemplate({ layer, selectedRole }).templateCode;
  });
}

const STALE_GRADI_LETTER_GROUPS: IntakeV6LetterGroupFinish[] = [
  {
    group_key: "pseudo:maria",
    layer_name: "pseudo maria (blue)",
    face_finish_type: "oracal_651",
    face_oracal_code: "053",
    face_oracal_name: "Light blue",
    return_finish_type: "ral_paint",
    return_depth_mm: 60,
    confirmed: true,
  },
  {
    group_key: "pseudo:soare",
    layer_name: "pseudo soare (red)",
    face_finish_type: "oracal_651",
    face_oracal_code: "047",
    face_oracal_name: "Orange red",
    return_finish_type: "white_aluminum",
    return_depth_mm: 60,
    confirmed: true,
  },
];

const STALE_GRADI_ARTWORK: IntakeV6ArtworkFinish[] = [
  {
    layer_key: "logo-stanga",
    layer_name: "logo stanga",
    execution_type: "print_laminate",
    color_mode: "polychrome",
    print_transparency: "translucent",
    return_finish_type: "white_aluminum",
    return_depth_mm: 60,
    confirmed: true,
  },
];

const DERIVED_FACE_GROUP: IntakeV6LetterGroupFinish = {
  group_key: "face:red",
  layer_name: "face red",
  source_fill_color: "#ff0000",
  face_finish_type: "none",
  face_oracal_code: null,
  face_oracal_name: null,
  return_finish_type: "white_aluminum",
  return_oracal_code: null,
  return_oracal_name: null,
  return_depth_mm: 40,
  face_vinyl_roll_width_mm: null,
  confirmed: false,
};

const SAVED_FACE_GROUP: IntakeV6LetterGroupFinish = {
  ...DERIVED_FACE_GROUP,
  face_finish_type: "oracal_8500",
  face_oracal_code: "083",
  face_oracal_name: "Nut brown",
  return_finish_type: "oracal_641",
  return_oracal_code: "070",
  return_oracal_name: "Black",
  return_depth_mm: 60,
  face_vinyl_roll_width_mm: 1260,
  confirmed: true,
};

describe("Intake V6 SVG analyzer file isolation and logo-only flow", () => {
  it("keeps required real SVG fixtures available", () => {
    for (const fileName of REQUIRED_FILES) {
      expect(readFileSync(resolve(SVG_DIR, fileName), "utf8").length).toBeGreaterThan(0);
    }
  });

  it("gradi-curat.svg can produce the four Ana Maria letter pseudo groups", () => {
    const report = analyzeFixture("gradi-curat.svg");

    expect(layerNames(report)).toEqual(
      expect.arrayContaining([
        "pseudo maria (blue)",
        "pseudo soare (red)",
        "pseudo ana (green)",
        "pseudo gradinita (orange)",
      ]),
    );
  });

  it("gradi-curat is treated as letters root with logo composition candidate", () => {
    const report = analyzeFixture("gradi-curat.svg");
    const confirmed = confirmAll(report);
    const templates = targetTemplates(report);
    const roles = confirmed.layers.map((layer) => layer.confirmedRole ?? layer.autoRole);
    const letterGroups = deriveLetterGroupsFromAnalyzer(report, confirmed);
    const artworkRows = deriveArtworkFinishesFromAnalyzer(report, confirmed);

    expect(roles).toEqual(expect.arrayContaining(["face", "printed_artwork"]));
    expect(letterGroups.length).toBeGreaterThan(0);
    expect(artworkRows.length).toBeGreaterThan(0);
    expect(artworkRows.some((row) => row.layer_key.includes("logo"))).toBe(true);

    expect(templates).toContain("TPL-VOLUMETRIC-LETTERS_v2");
    expect(templates).toContain("TPL-VOLUMETRIC-LOGO_v1");
    expect(templates.every((template) => template === "TPL-VOLUMETRIC-LOGO_v1")).toBe(false);
    expect(templates.every((template) => template === "TPL-VOLUMETRIC-LETTERS_v2")).toBe(false);
  });

  it.each(["litere-vol-1-layer.svg", "litere-vol-2-layere.svg", "logo.svg"] as const)(
    "%s does not inherit gradi-curat pseudo groups",
    (fileName) => {
      const report = analyzeFixture(fileName);

      for (const staleName of [
        "pseudo maria (blue)",
        "pseudo soare (red)",
        "pseudo ana (green)",
        "pseudo gradinita (orange)",
      ]) {
        expect(layerNames(report)).not.toContain(staleName);
      }
    },
  );

  it("does not merge stale gradi letter finish rows onto a different current analyzer result", () => {
    const report = analyzeFixture("litere-vol-1-layer.svg");
    const derived = deriveLetterGroupsFromAnalyzer(report, confirmAll(report));
    const merged = mergeLetterGroupFinishes(derived, STALE_GRADI_LETTER_GROUPS);

    expect(merged.map((row) => row.group_key)).not.toEqual(
      expect.arrayContaining(["pseudo:maria", "pseudo:soare"]),
    );
    expect(merged.some((row) => row.confirmed)).toBe(false);
  });

  it("preserves saved letter group values when source fill matches with trim/case tolerance", () => {
    const merged = mergeLetterGroupFinishes(
      [{ ...DERIVED_FACE_GROUP, source_fill_color: "  #FF0000  " }],
      [SAVED_FACE_GROUP],
    );

    expect(merged).toHaveLength(1);
    expect(merged[0]).toMatchObject({
      face_finish_type: "oracal_8500",
      face_oracal_code: "083",
      face_oracal_name: "Nut brown",
      return_finish_type: "oracal_641",
      return_oracal_code: "070",
      return_oracal_name: "Black",
      return_depth_mm: 60,
      face_vinyl_roll_width_mm: 1260,
      confirmed: true,
    });
  });

  it("resets stale saved letter group values when source fill changes", () => {
    const changedDerived = { ...DERIVED_FACE_GROUP, source_fill_color: "#00ff00" };
    const merged = mergeLetterGroupFinishes([changedDerived], [SAVED_FACE_GROUP]);
    const derivedOnly = mergeLetterGroupFinishes([changedDerived], undefined);

    expect(merged).toHaveLength(1);
    expect(derivedOnly[0]).toMatchObject({
      face_finish_type: "none",
      face_oracal_code: null,
      face_oracal_name: null,
      return_finish_type: "white_aluminum",
      return_depth_mm: 40,
      confirmed: false,
    });
    expect(merged[0]?.confirmed).toBe(false);
    expect(merged[0]?.face_finish_type).toBe("oracal_651");
    expect(merged[0]?.face_finish_type).not.toBe(SAVED_FACE_GROUP.face_finish_type);
    expect(merged[0]?.face_oracal_code).not.toBe(SAVED_FACE_GROUP.face_oracal_code);
    expect(merged[0]?.return_finish_type).toBe(DERIVED_FACE_GROUP.return_finish_type);
    expect(merged[0]?.return_depth_mm).toBe(DERIVED_FACE_GROUP.return_depth_mm);
  });

  it("does not merge stale gradi artwork rows onto logo.svg unless keys match current logo analysis", () => {
    const report = analyzeFixture("logo.svg");
    const derived = deriveArtworkFinishesFromAnalyzer(report, confirmAll(report));
    const merged = mergeArtworkFinishes(derived, STALE_GRADI_ARTWORK);

    expect(merged.map((row) => row.layer_key)).not.toEqual(expect.arrayContaining(["pseudo:maria"]));
  });

  it("logo.svg produces a logo/artwork template candidate without commercial offerability activation", () => {
    const report = analyzeFixture("logo.svg");
    const templates = targetTemplates(report);

    expect(templates).toContain("TPL-VOLUMETRIC-LOGO_v1");
    expect(layerNames(report)).not.toEqual(expect.arrayContaining(["pseudo maria (blue)"]));
  });

  it("logo.svg can complete Pas 1 layer roles as safe artwork/logo without forcing Vector Litere", () => {
    const report = analyzeFixture("logo.svg");
    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    const roles = confirmed.layers.map((layer) => layer.confirmedRole ?? layer.autoRole);
    const letterGroups = deriveLetterGroupsFromAnalyzer(report, confirmed);
    const artworkRows = deriveArtworkFinishesFromAnalyzer(report, confirmed);

    expect(confirmed.confirmationStatus).toBe("complete");
    expect(roles).toEqual(expect.arrayContaining(["printed_artwork"]));
    expect(roles).not.toContain("face");
    expect(letterGroups).toEqual([]);
    expect(artworkRows.map((row) => row.layer_key)).toContain("logo-dreapta");
    expect(targetTemplates(report)).toContain("TPL-VOLUMETRIC-LOGO_v1");
  });
});