import type { IntakeV4ArtworkFinish } from "@/lib/intakeV6/intakeV4ArtworkFinish";
import type { IntakeV4FinishSetup } from "@/lib/intakeV6/intakeV4Api";
import { normalizeFaceVinylRollWidthMm } from "@/lib/intakeV6/intakeV4FaceFinishOptions";
import type { IntakeV4LetterGroupFinish } from "@/lib/intakeV6/intakeV4LetterGroups";
import {
  layerFinishesHaveExplicitBacking,
  normalizeIntakeV4BackingMode,
} from "@/lib/intakeV6/intakeV4BackingMode";

function dominantToken(values: Array<string | null | undefined>, fallback: string | undefined): string | undefined {
  const cleaned = values.map((v) => (v ?? "").trim()).filter(Boolean);
  if (cleaned.length === 0) return fallback;
  const counts = new Map<string, number>();
  for (const token of cleaned) {
    counts.set(token, (counts.get(token) ?? 0) + 1);
  }
  let best = cleaned[0];
  let bestCount = 0;
  for (const [token, count] of counts) {
    if (count > bestCount) {
      best = token;
      bestCount = count;
    }
  }
  return best;
}

function dominantNumber(
  values: Array<number | null | undefined>,
  fallback: number | null | undefined,
): number | null | undefined {
  const cleaned = values.filter((v): v is number => typeof v === "number" && Number.isFinite(v) && v > 0);
  if (cleaned.length === 0) return fallback;
  const counts = new Map<number, number>();
  for (const value of cleaned) {
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  let best = cleaned[0];
  let bestCount = 0;
  for (const [value, count] of counts) {
    if (count > bestCount) {
      best = value;
      bestCount = count;
    }
  }
  return best;
}

/** Mirror backend normalize — keep job-level finish fields aligned with per-layer selections. */
export function syncIntakeV4FinishPayloadFromLayerFinishes(
  form: IntakeV4FinishSetup,
  letterGroups: IntakeV4LetterGroupFinish[],
  artworkFinishes: IntakeV4ArtworkFinish[],
): IntakeV4FinishSetup {
  if (letterGroups.length === 0 && artworkFinishes.length === 0) {
    return form;
  }

  const next: IntakeV4FinishSetup = { ...form };

  if (letterGroups.length > 0) {
    const face = dominantToken(
      letterGroups.map((g) => g.face_finish_type),
      form.face_finish_type,
    );
    const ret = dominantToken(
      letterGroups.map((g) => g.return_finish_type),
      form.return_finish_type,
    );
    const depths = letterGroups
      .map((g) => g.return_depth_mm)
      .filter((d): d is number => d != null && Number.isFinite(d));
    if (face) next.face_finish_type = face;
    next.face_vinyl_roll_width_mm = normalizeFaceVinylRollWidthMm(
      next.face_finish_type,
      dominantNumber(
        letterGroups.map((g) => g.face_vinyl_roll_width_mm),
        form.face_vinyl_roll_width_mm,
      ),
    );
    if (ret) next.return_finish_type = ret;
    if (depths.length > 0) next.return_depth_mm = Math.max(...depths);
  } else if (artworkFinishes.length > 0) {
    const ret = dominantToken(
      artworkFinishes.map((a) => a.return_finish_type),
      form.return_finish_type,
    );
    const depths = artworkFinishes
      .map((a) => a.return_depth_mm)
      .filter((d): d is number => d != null && Number.isFinite(d));
    if (ret) next.return_finish_type = ret;
    if (depths.length > 0) next.return_depth_mm = Math.max(...depths);
  }

  if (layerFinishesHaveExplicitBacking(letterGroups, artworkFinishes)) {
    const globalMode = normalizeIntakeV4BackingMode(form.backing_mode);
    next.letter_group_finishes = letterGroups.map((group) => ({
      ...group,
      backing_mode: group.backing_mode ?? globalMode,
    }));
    next.artwork_finishes = artworkFinishes.map((row) => ({
      ...row,
      backing_mode: row.backing_mode ?? globalMode,
    }));
    delete next.backing_mode;
    delete next.back_bevel_enabled;
  }

  return next;
}

export function finishSetupIdentityKey(args: {
  form: IntakeV4FinishSetup;
  letterGroups: IntakeV4LetterGroupFinish[];
  artworkFinishes: IntakeV4ArtworkFinish[];
  workspaceUpdatedAt?: string | null;
}): string {
  return JSON.stringify({
    updated_at: args.workspaceUpdatedAt ?? null,
    form: {
      face_finish_type: args.form.face_finish_type,
      face_vinyl_roll_width_mm: args.form.face_vinyl_roll_width_mm,
      return_finish_type: args.form.return_finish_type,
      return_oracal_code: args.form.return_oracal_code,
      return_oracal_name: args.form.return_oracal_name,
      return_depth_mm: args.form.return_depth_mm,
      illuminated: args.form.illuminated,
      lighting_system_type: args.form.lighting_system_type,
      light_color: args.form.light_color,
      led_module_power_w: args.form.led_module_power_w,
      led_strip_power_w_per_ml: args.form.led_strip_power_w_per_ml,
      letter_led_strip_length_m: args.form.letter_led_strip_length_m,
      emblem_led_strip_length_m: args.form.emblem_led_strip_length_m,
      total_led_strip_length_m: args.form.total_led_strip_length_m,
      selected_psu_watts: args.form.selected_psu_watts,
      backing_mode: args.form.backing_mode,
      back_bevel_enabled: args.form.back_bevel_enabled,
      emblem_lighting_mode: args.form.emblem_lighting_mode,
      mounting_template_enabled: args.form.mounting_template_enabled,
      mounting_template_area_m2: args.form.mounting_template_area_m2,
      mounting_template_material_type: args.form.mounting_template_material_type,
      mounting_system: args.form.mounting_system,
      mounting_bar_profile: args.form.mounting_bar_profile,
      mounting_scope: args.form.mounting_scope,
      site_installation_included: args.form.site_installation_included,
      volum_aluminum_module_template_code: args.form.volum_aluminum_module_template_code,
      confirmed: args.form.confirmed,
    },
    letterGroups: args.letterGroups,
    artworkFinishes: args.artworkFinishes,
  });
}
