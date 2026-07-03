import type { IntakeV4ArtworkFinish } from "@/lib/intakeV6/intakeV4ArtworkFinish";
import type { IntakeV4FinishSetup } from "@/lib/intakeV6/intakeV4Api";
import type { IntakeV4LetterGroupFinish } from "@/lib/intakeV6/intakeV4LetterGroups";
import { INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE as INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE } from "@/lib/intakeV6/intakeV6ReturnFinishOptions";
import type {
  LetterGroupReturnCantFinish,
  LetterGroupReturnFinishType,
} from "@/lib/intakeV6/intakeV6ReturnFinishModel";

function resolveStoredReturnFinishType(
  stored: string | null | undefined,
): LetterGroupReturnFinishType {
  const token = String(stored ?? "").trim();
  if (token) return token as LetterGroupReturnFinishType;
  return INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE as LetterGroupReturnFinishType;
}

export function letterGroupToReturnCant(
  group: Pick<
    IntakeV4LetterGroupFinish,
    "return_finish_type" | "return_depth_mm" | "return_oracal_code" | "return_oracal_name"
  >,
): LetterGroupReturnCantFinish {
  const finishType = resolveStoredReturnFinishType(group.return_finish_type);
  const needsColor = finishType === "oracal_wrapped" || finishType === "ral_paint";
  return {
    finishType,
    depthMm: group.return_depth_mm ?? undefined,
    materialCode:
      finishType === "oracal_wrapped" ? "651" : finishType === "ral_paint" ? "RAL" : undefined,
    colorCode: needsColor ? group.return_oracal_code ?? undefined : undefined,
    colorName: needsColor ? group.return_oracal_name ?? undefined : undefined,
  };
}

export function patchLetterGroupFromReturnCant(
  cant: LetterGroupReturnCantFinish,
): Pick<
  IntakeV4LetterGroupFinish,
  "return_finish_type" | "return_depth_mm" | "return_oracal_code" | "return_oracal_name"
> {
  const needsColor = cant.finishType === "oracal_wrapped" || cant.finishType === "ral_paint";
  return {
    return_finish_type: cant.finishType,
    return_depth_mm: cant.depthMm ?? null,
    return_oracal_code: needsColor ? cant.colorCode ?? null : null,
    return_oracal_name: needsColor ? cant.colorName ?? null : null,
  };
}

export function artworkToReturnCant(
  row: Pick<
    IntakeV4ArtworkFinish,
    "return_finish_type" | "return_depth_mm" | "return_oracal_code" | "return_oracal_name"
  >,
): LetterGroupReturnCantFinish {
  const finishType = resolveStoredReturnFinishType(row.return_finish_type);
  const needsColor = finishType === "oracal_wrapped" || finishType === "ral_paint";
  return {
    finishType,
    depthMm: row.return_depth_mm ?? undefined,
    materialCode:
      finishType === "oracal_wrapped" ? "651" : finishType === "ral_paint" ? "RAL" : undefined,
    colorCode: needsColor ? row.return_oracal_code ?? undefined : undefined,
    colorName: needsColor ? row.return_oracal_name ?? undefined : undefined,
  };
}

export function patchArtworkFromReturnCant(
  cant: LetterGroupReturnCantFinish,
): Pick<
  IntakeV4ArtworkFinish,
  "return_finish_type" | "return_depth_mm" | "return_oracal_code" | "return_oracal_name"
> {
  const needsColor = cant.finishType === "oracal_wrapped" || cant.finishType === "ral_paint";
  return {
    return_finish_type: cant.finishType,
    return_depth_mm: cant.depthMm ?? null,
    return_oracal_code: needsColor ? cant.colorCode ?? null : null,
    return_oracal_name: needsColor ? cant.colorName ?? null : null,
  };
}

/** Per-layer SVG export — global față/cant forms are compatibility fallback only (V2 pattern). */
export function shouldHideGlobalFinishSettings(args: {
  letterGroupCount: number;
  artworkCount: number;
}): boolean {
  return args.letterGroupCount > 0 || args.artworkCount > 0;
}

export function globalFinishSetupToReturnCant(
  setup: Pick<
    IntakeV4FinishSetup,
    "return_finish_type" | "return_depth_mm" | "return_oracal_code" | "return_oracal_name"
  >,
): LetterGroupReturnCantFinish {
  return letterGroupToReturnCant({
    return_finish_type: setup.return_finish_type,
    return_depth_mm: setup.return_depth_mm,
    return_oracal_code: setup.return_oracal_code,
    return_oracal_name: setup.return_oracal_name,
  });
}

export function patchGlobalFinishSetupFromReturnCant(
  cant: LetterGroupReturnCantFinish,
): Pick<
  IntakeV4FinishSetup,
  "return_finish_type" | "return_depth_mm" | "return_oracal_code" | "return_oracal_name"
> {
  return patchLetterGroupFromReturnCant(cant);
}
