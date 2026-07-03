import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";
import { faceFinishNeedsColorPicker } from "@/lib/intakeV6/intakeV6FaceFinishOptions";
import {
  INTAKE_V6_RETURN_FINISH_UI_OPTIONS,
  resolveIntakeV6ReturnFinishUiOption,
} from "@/lib/intakeV6/intakeV6ReturnFinishOptions";

export function layerAccentColor(fill: string | null | undefined): string {
  const raw = fill?.trim();
  if (!raw) return "#64748b";
  if (/^#[0-9a-f]{3,8}$/i.test(raw) || /^rgb/i.test(raw)) return raw;
  return "#64748b";
}

export function faceFinishLabel(
  faceFinishType: string,
  options: readonly { value: string; label: string }[],
): string {
  return options.find((row) => row.value === faceFinishType)?.label ?? faceFinishType;
}

export function cantFinishLabel(returnFinishType: string | null | undefined): string {
  const ui = resolveIntakeV6ReturnFinishUiOption(returnFinishType);
  return INTAKE_V6_RETURN_FINISH_UI_OPTIONS.find((row) => row.value === ui)?.label ?? "—";
}

export function buildFaceSummaryLine(
  group: IntakeV6LetterGroupFinish,
  faceOptions: readonly { value: string; label: string }[],
): string {
  const finish = faceFinishLabel(group.face_finish_type, faceOptions);
  if (!faceFinishNeedsColorPicker(group.face_finish_type)) {
    return finish;
  }
  const code = group.face_oracal_code?.trim();
  const name = group.face_oracal_name?.trim();
  if (code && name) return `${finish} · ${code} ${name}`;
  if (code) return `${finish} · ${code}`;
  return `${finish} · culoare lipsă`;
}

export function buildCantSummaryLine(group: IntakeV6LetterGroupFinish): string {
  const finish = cantFinishLabel(group.return_finish_type);
  const depth = group.return_depth_mm != null ? `${group.return_depth_mm} mm` : "— mm";
  return `${finish} · ${depth}`;
}

export type LayerCardStatus = "ok" | "warning" | null;

export function resolveLayerCardStatus(group: IntakeV6LetterGroupFinish): LayerCardStatus {
  if (faceFinishNeedsColorPicker(group.face_finish_type) && !group.face_oracal_code?.trim()) {
    return "warning";
  }
  const ui = resolveIntakeV6ReturnFinishUiOption(group.return_finish_type);
  if (ui === "ral_paint" || ui === "oracal_wrapped") {
    if (!group.return_oracal_code?.trim()) return "warning";
  }
  if (group.confirmed) return "ok";
  return null;
}
