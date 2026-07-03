import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import type { ColorRegistryItem } from "@/lib/colorRegistry/colorRegistryTypes";

export function patchReturnRalSelection(
  spec: IntakeProductSpec,
  item: ColorRegistryItem
): Partial<IntakeProductSpec> {
  return {
    return_finish_system: "RAL",
    return_ral_code: item.code,
    return_ral_name: item.romanianName ?? item.name,
    return_ral_preview_hex: item.previewHex,
    return_oracal_series: undefined,
    return_oracal_code: undefined,
    return_oracal_name: undefined,
    return_oracal_preview_hex: undefined,
    paint_ral_code: item.code,
    paint_ral_name: item.romanianName ?? item.name,
  };
}

export function patchReturnOracalSelection(
  spec: IntakeProductSpec,
  item: ColorRegistryItem
): Partial<IntakeProductSpec> {
  return {
    return_finish_system: "ORACAL",
    return_oracal_series: item.series ?? "651",
    return_oracal_code: item.code,
    return_oracal_name: item.name,
    return_oracal_preview_hex: item.previewHex,
    return_ral_code: undefined,
    return_ral_name: undefined,
    return_ral_preview_hex: undefined,
  };
}

export function patchReturnStandardSelection(
  color: "white" | "black"
): Partial<IntakeProductSpec> {
  return {
    return_finish_system: "standard",
    return_color: color,
    return_edge_color: color,
    return_ral_code: undefined,
    return_ral_name: undefined,
    return_ral_preview_hex: undefined,
    return_oracal_series: undefined,
    return_oracal_code: undefined,
    return_oracal_name: undefined,
    return_oracal_preview_hex: undefined,
  };
}

export function patchFaceVinylSelection(
  item: ColorRegistryItem
): Partial<IntakeProductSpec> {
  const series = item.series ?? "651";
  const faceFinishType = series === "8500" ? "oracal_8500" : "oracal_651";
  const vinylFinish =
    series === "8500"
      ? ("translucent_matte" as const)
      : item.finish === "matte"
        ? ("matte" as const)
        : ("gloss" as const);

  return {
    face_vinyl_enabled: true,
    face_wrap_enabled: true,
    face_vinyl_series: series,
    face_vinyl_code: item.code,
    face_vinyl_name: item.name,
    face_vinyl_preview_hex: item.previewHex,
    face_vinyl_finish: vinylFinish,
    face_finish_type: faceFinishType,
    face_vinyl_color_code: `${series}-${item.code}`,
    face_vinyl_color_name: item.name,
  };
}

export function clearFaceVinylColorSelection(): Partial<IntakeProductSpec> {
  return {
    face_vinyl_code: undefined,
    face_vinyl_name: undefined,
    face_vinyl_preview_hex: undefined,
    face_vinyl_color_code: undefined,
    face_vinyl_color_name: undefined,
  };
}

export function isReturnFinishComplete(spec: IntakeProductSpec | null | undefined): boolean {
  if (!spec) return false;
  const system = spec.return_finish_system ?? "standard";
  if (system === "standard") {
    return (
      spec.return_color === "white" ||
      spec.return_color === "black" ||
      spec.return_edge_color === "white" ||
      spec.return_edge_color === "black"
    );
  }
  if (system === "RAL") return Boolean(spec.return_ral_code?.trim());
  if (system === "ORACAL") {
    return Boolean(spec.return_oracal_code?.trim() && spec.return_oracal_series);
  }
  return false;
}
