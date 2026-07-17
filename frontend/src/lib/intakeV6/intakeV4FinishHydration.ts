import type { IntakeV4ArtworkFinish } from "./intakeV4ArtworkFinish";
import { artworkFinishesFromPayload } from "./intakeV4ArtworkFinish";
import type { IntakeV4FinishSetup } from "./intakeV4Api";
import { normalizeFaceVinylRollWidthMm } from "./intakeV4FaceFinishOptions";
import type { IntakeV4LetterGroupFinish } from "./intakeV4LetterGroups";
import { letterGroupFinishesFromPayload } from "./intakeV4LetterGroups";
import {
  normalizeEmblemLightingMode,
  normalizeIntakeV4BackingMode,
  type IntakeV4BackingMode,
  type IntakeV4EmblemLightingMode,
} from "./intakeV4BackingMode";
import { normalizeIntakeV4LedModuleWattage } from "./intakeV4LedLighting";

export const INTAKE_V4_PENDING_SAVE_BANNER =
  "Ai modificari in curs de sincronizare. Preturile si materialele se actualizeaza automat.";

export function readFinishSetupFromPayload(
  payload: Record<string, unknown> | undefined,
): IntakeV4FinishSetup | null {
  const raw = payload?.finish_setup;
  if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return null;
  return raw as IntakeV4FinishSetup;
}

export function savedBackingModeFromPayload(
  payload: Record<string, unknown> | undefined,
): IntakeV4BackingMode {
  const setup = readFinishSetupFromPayload(payload);
  return normalizeIntakeV4BackingMode(setup?.backing_mode);
}

export function savedEmblemLightingFromPayload(
  payload: Record<string, unknown> | undefined,
): IntakeV4EmblemLightingMode {
  const setup = readFinishSetupFromPayload(payload);
  return normalizeEmblemLightingMode(setup?.emblem_lighting_mode);
}

export function savedReturnFinishFromPayload(payload: Record<string, unknown> | undefined): string {
  const setup = readFinishSetupFromPayload(payload);
  return String(setup?.return_finish_type ?? "").trim();
}

function normalizeLetterGroupForCompare(group: IntakeV4LetterGroupFinish) {
  return {
    group_key: group.group_key,
    face_finish_type: String(group.face_finish_type ?? "").trim(),
    face_oracal_code: group.face_oracal_code ?? null,
    face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
      group.face_finish_type,
      group.face_vinyl_roll_width_mm,
    ),
    return_finish_type: String(group.return_finish_type ?? "").trim(),
    return_depth_mm: group.return_depth_mm ?? null,
    return_oracal_code: group.return_oracal_code ?? null,
    return_oracal_name: group.return_oracal_name ?? null,
    backing_mode: group.backing_mode ?? null,
  };
}

function normalizeArtworkForCompare(row: IntakeV4ArtworkFinish) {
  return {
    layer_key: row.layer_key,
    execution_type: row.execution_type,
    color_mode: row.color_mode,
    print_transparency: row.print_transparency ?? "standard",
    return_finish_type: String(row.return_finish_type ?? "").trim(),
    return_depth_mm: row.return_depth_mm ?? null,
    return_oracal_code: row.return_oracal_code ?? null,
    backing_mode: row.backing_mode ?? null,
  };
}

function normalizeFinishFormForCompare(form: IntakeV4FinishSetup) {
  return {
    backing_mode: normalizeIntakeV4BackingMode(form.backing_mode),
    emblem_lighting_mode: normalizeEmblemLightingMode(form.emblem_lighting_mode),
    illuminated: form.illuminated !== false,
    lighting_system_type: String(form.lighting_system_type ?? "led_modules").trim(),
    light_color: String(form.light_color ?? "neutral").trim(),
    led_module_power_w: normalizeIntakeV4LedModuleWattage(form.led_module_power_w),
    led_strip_power_w_per_ml: form.led_strip_power_w_per_ml ?? 5,
    letter_led_strip_length_m: form.letter_led_strip_length_m ?? null,
    emblem_led_strip_length_m: form.emblem_led_strip_length_m ?? null,
    total_led_strip_length_m: form.total_led_strip_length_m ?? null,
    face_finish_type: String(form.face_finish_type ?? "").trim(),
    face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
      form.face_finish_type,
      form.face_vinyl_roll_width_mm,
    ),
    return_finish_type: String(form.return_finish_type ?? "").trim(),
    return_depth_mm: form.return_depth_mm ?? null,
    mounting_scope: form.mounting_scope ?? null,
    site_installation_included: form.site_installation_included ?? null,
    mounting_template_enabled: form.mounting_template_enabled ?? null,
    mounting_template_area_m2: form.mounting_template_area_m2 ?? null,
    mounting_template_material_type: form.mounting_template_material_type ?? null,
    mounting_system: form.mounting_system ?? null,
    mounting_bar_profile: form.mounting_bar_profile ?? null,
    mains_cable_length_m: form.mains_cable_length_m ?? null,
    power_supply_service_corner: form.power_supply_service_corner ?? null,
    service_screw_finish: form.service_screw_finish ?? null,
    volum_aluminum_module_template_code: form.volum_aluminum_module_template_code ?? null,
    confirmed: form.confirmed === true,
  };
}

function layerFinishesEqual<T>(
  current: T[],
  saved: T[],
  normalize: (item: T) => unknown,
): boolean {
  if (current.length !== saved.length) return false;
  const savedByKey = new Map(
    saved.map((item) => {
      const normalized = normalize(item) as { group_key?: string; layer_key?: string };
      const key = normalized.group_key ?? normalized.layer_key ?? "";
      return [key, normalize(item)] as const;
    }),
  );
  for (const item of current) {
    const normalized = normalize(item) as { group_key?: string; layer_key?: string };
    const key = normalized.group_key ?? normalized.layer_key ?? "";
    const prior = savedByKey.get(key);
    if (!prior || JSON.stringify(prior) !== JSON.stringify(normalized)) {
      return false;
    }
  }
  return true;
}

/** True when operator changed selectors that preview APIs read from persisted workspace only. */
export function isIntakeV4SelectorStatePendingSave(
  form: IntakeV4FinishSetup,
  payload: Record<string, unknown> | undefined,
  letterGroups: IntakeV4LetterGroupFinish[] = [],
  artworkFinishes: IntakeV4ArtworkFinish[] = [],
  options?: {
    /** Hydrated form baseline (e.g. syncLighting + mounting template) — remount/HMR safe. */
    expectedForm?: IntakeV4FinishSetup;
    /** Merged letter baseline matching Review local init (derive+payload). */
    expectedLetterGroups?: IntakeV4LetterGroupFinish[];
    /** Merged artwork baseline matching Review local init (derive+payload). */
    expectedArtworkFinishes?: IntakeV4ArtworkFinish[];
  },
): boolean {
  const setup = readFinishSetupFromPayload(payload);
  if (!setup) return true;
  if (setup.confirmed !== true) return true;

  const baselineForm = options?.expectedForm ?? setup;
  const savedForm = normalizeFinishFormForCompare(baselineForm);
  const currentForm = normalizeFinishFormForCompare(form);
  if (JSON.stringify(savedForm) !== JSON.stringify(currentForm)) {
    return true;
  }

  const savedLetterGroups =
    options?.expectedLetterGroups ?? letterGroupFinishesFromPayload(payload);
  if (!layerFinishesEqual(letterGroups, savedLetterGroups, normalizeLetterGroupForCompare)) {
    return true;
  }

  const savedArtworkFinishes =
    options?.expectedArtworkFinishes ?? artworkFinishesFromPayload(payload);
  if (!layerFinishesEqual(artworkFinishes, savedArtworkFinishes, normalizeArtworkForCompare)) {
    return true;
  }

  return false;
}

/** Key for refetching persisted preview/breakdown — workspace revision only, not local form edits. */
export function intakeV4PersistedReviewRefetchKey(args: {
  workspaceUpdatedAt?: string | null;
  footprintOverrideRevision?: number;
}): string {
  return `${args.workspaceUpdatedAt ?? "none"}:${args.footprintOverrideRevision ?? 0}`;
}
