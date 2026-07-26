/**
 * ACM shell Finish Contract (face ≠ volume foil) — nested on acm_panel_instance.
 * MIXED §7–8 / PS teaching. Not letter face_finish_type. Not CostEngine.
 */

import {
  INTAKE_V4_DEFAULT_ORACAL_FACE_ROLL_WIDTH_MM,
  INTAKE_V4_DEFAULT_PRINT_LAMINATION_ROLL_WIDTH_MM,
  INTAKE_V4_ORACAL_FACE_ROLL_WIDTH_OPTIONS,
  PRINT_LAMINATION_ROLL_WIDTHS_MM,
} from "@/lib/intakeV6/intakeV4FaceFinishOptions";

export const ACM_SHELL_FINISH_SCHEMA = "acm_shell_finish_v1" as const;

export type AcmShellZoneKind = "stock_plate" | "oracal_651" | "print_laminate";

export type AcmShellZoneFinish =
  | { kind: "stock_plate" }
  | {
      kind: "oracal_651";
      color_code: string;
      color_name?: string | null;
      roll_width_mm: 1000 | 1260;
    }
  | {
      kind: "print_laminate";
      roll_width_mm: 1050 | 1320 | 1500;
    };

export type AcmShellFoilStrategyMode =
  | "face_plus_first_fold"
  | "face_one_piece_volume_separate"
  | "face_multi_piece";

export type AcmShellFoilStrategy =
  | { mode: "face_plus_first_fold" }
  | { mode: "face_one_piece_volume_separate" }
  | {
      mode: "face_multi_piece";
      piece_count: number;
      client_informed: boolean;
    };

export type AcmShellFinishContract = {
  schema: typeof ACM_SHELL_FINISH_SCHEMA;
  face: AcmShellZoneFinish;
  volume: AcmShellZoneFinish;
  foil_strategy: AcmShellFoilStrategy | null;
  /** Invariant teaching: colant after frame — always true when foil present. */
  apply_after_frame: boolean;
  /** XOR with any vinyl/print on face or volume. */
  paint_screws_if_no_foil: boolean;
  operator_confirmed: boolean;
};

export const ACM_SHELL_ZONE_KIND_OPTIONS: readonly {
  value: AcmShellZoneKind;
  labelRo: string;
}[] = [
  { value: "stock_plate", labelRo: "Placă stock (fără colant)" },
  { value: "oracal_651", labelRo: "Oracal 651" },
  { value: "print_laminate", labelRo: "Print + laminare" },
] as const;

export const ACM_SHELL_FOIL_STRATEGY_OPTIONS: readonly {
  value: AcmShellFoilStrategyMode;
  labelRo: string;
}[] = [
  { value: "face_plus_first_fold", labelRo: "1 — Față + primul pliu" },
  { value: "face_one_piece_volume_separate", labelRo: "2 — Față o bucată · volum separat" },
  { value: "face_multi_piece", labelRo: "3 — Față multi-bucăți (client informat)" },
] as const;

export function zoneNeedsFoil(zone: AcmShellZoneFinish | null | undefined): boolean {
  const kind = zone?.kind;
  return kind === "oracal_651" || kind === "print_laminate";
}

export function shellNeedsFoil(finish: AcmShellFinishContract | null | undefined): boolean {
  if (!finish) return false;
  return zoneNeedsFoil(finish.face) || zoneNeedsFoil(finish.volume);
}

export function defaultAcmShellZone(kind: AcmShellZoneKind = "stock_plate"): AcmShellZoneFinish {
  if (kind === "oracal_651") {
    return {
      kind: "oracal_651",
      color_code: "",
      color_name: null,
      roll_width_mm: INTAKE_V4_DEFAULT_ORACAL_FACE_ROLL_WIDTH_MM as 1000,
    };
  }
  if (kind === "print_laminate") {
    return {
      kind: "print_laminate",
      roll_width_mm: INTAKE_V4_DEFAULT_PRINT_LAMINATION_ROLL_WIDTH_MM as 1050,
    };
  }
  return { kind: "stock_plate" };
}

export function defaultAcmShellFinishContract(): AcmShellFinishContract {
  return {
    schema: ACM_SHELL_FINISH_SCHEMA,
    face: defaultAcmShellZone("stock_plate"),
    volume: defaultAcmShellZone("stock_plate"),
    foil_strategy: null,
    apply_after_frame: true,
    paint_screws_if_no_foil: true,
    operator_confirmed: false,
  };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function parseZone(raw: unknown): AcmShellZoneFinish {
  const rec = asRecord(raw);
  const kind = String(rec?.kind ?? "stock_plate").trim().toLowerCase();
  if (kind === "oracal_651") {
    const width = Number(rec?.roll_width_mm);
    const allowed = INTAKE_V4_ORACAL_FACE_ROLL_WIDTH_OPTIONS.map((o) => o.value);
    const roll_width_mm = (allowed.includes(width as 1000) ? width : 1000) as 1000 | 1260;
    return {
      kind: "oracal_651",
      color_code: String(rec?.color_code ?? "").trim(),
      color_name: rec?.color_name != null ? String(rec.color_name) : null,
      roll_width_mm,
    };
  }
  if (kind === "print_laminate") {
    const width = Number(rec?.roll_width_mm);
    const roll_width_mm = (
      PRINT_LAMINATION_ROLL_WIDTHS_MM.includes(width as 1050) ? width : 1050
    ) as 1050 | 1320 | 1500;
    return { kind: "print_laminate", roll_width_mm };
  }
  return { kind: "stock_plate" };
}

function parseStrategy(raw: unknown, needsFoil: boolean): AcmShellFoilStrategy | null {
  if (!needsFoil) return null;
  const rec = asRecord(raw);
  const mode = String(rec?.mode ?? "face_plus_first_fold").trim();
  if (mode === "face_one_piece_volume_separate") {
    return { mode: "face_one_piece_volume_separate" };
  }
  if (mode === "face_multi_piece") {
    const piece_count = Math.max(2, Math.floor(Number(rec?.piece_count) || 2));
    return {
      mode: "face_multi_piece",
      piece_count,
      client_informed: Boolean(rec?.client_informed),
    };
  }
  return { mode: "face_plus_first_fold" };
}

/** Normalize unknown payload → contract (never invents confirmed). */
export function normalizeAcmShellFinish(raw: unknown): AcmShellFinishContract {
  const rec = asRecord(raw);
  if (!rec) return defaultAcmShellFinishContract();
  const face = parseZone(rec.face);
  const volume = parseZone(rec.volume);
  const needs = zoneNeedsFoil(face) || zoneNeedsFoil(volume);
  const foil_strategy = parseStrategy(rec.foil_strategy, needs);
  return {
    schema: ACM_SHELL_FINISH_SCHEMA,
    face,
    volume,
    foil_strategy,
    apply_after_frame: true,
    paint_screws_if_no_foil: !needs,
    operator_confirmed: Boolean(rec.operator_confirmed),
  };
}

export function readAcmShellFinishFromInstance(instance: {
  shell_finish?: unknown;
}): AcmShellFinishContract {
  return normalizeAcmShellFinish(instance.shell_finish);
}

export function zoneKindLabelRo(kind: AcmShellZoneKind): string {
  return ACM_SHELL_ZONE_KIND_OPTIONS.find((o) => o.value === kind)?.labelRo ?? kind;
}

export function summarizeAcmShellFinishRo(finish: AcmShellFinishContract): string {
  const face = zoneKindLabelRo(finish.face.kind);
  const volume = zoneKindLabelRo(finish.volume.kind);
  if (!shellNeedsFoil(finish)) {
    return `Față: ${face} · Volum: ${volume} · vopsire șuruburi (fără colant)`;
  }
  const strat =
    ACM_SHELL_FOIL_STRATEGY_OPTIONS.find((o) => o.value === finish.foil_strategy?.mode)
      ?.labelRo ?? "strategie folie";
  return `Față: ${face} · Volum: ${volume} · ${strat} · colant după cadru`;
}

/** Short operator-facing line — no foil-strategy essay. */
export function summarizeAcmShellFinishOperatorRo(finish: AcmShellFinishContract): string {
  if (!shellNeedsFoil(finish)) {
    return "Fără colant · vopsire șuruburi";
  }
  const zones: string[] = [];
  if (zoneNeedsFoil(finish.face)) zones.push("față");
  if (zoneNeedsFoil(finish.volume)) zones.push("cant");
  const where = zones.length ? zones.join(" + ") : "folie";
  return `Colant ${where} · după cadru`;
}
