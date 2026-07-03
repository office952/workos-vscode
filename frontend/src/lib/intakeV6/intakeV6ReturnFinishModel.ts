import { lookupColorRegistryItem } from "@/lib/colorRegistry/colorRegistry";
import { ALLOWED_RETURN_DEPTH_MM } from "@/lib/volumetricQuoteInput";

export type LetterGroupReturnFinishType =
  | "same_as_face"
  | "oracal_wrapped"
  | "ral_paint"
  | "standard_aluminum"
  | "black_aluminum"
  | "white_aluminum"
  | "mirror_silver"
  | "none";

export interface LetterGroupReturnCantFinish {
  finishType: LetterGroupReturnFinishType;
  depthMm?: number;
  materialCode?: string;
  colorCode?: string;
  colorName?: string;
  notes?: string;
}

type IntakeV6ReturnBuildFinishType = LetterGroupReturnFinishType | "gold_aluminum";

export function buildReturnForFinishType(
  finishType: IntakeV6ReturnBuildFinishType,
  prev: LetterGroupReturnCantFinish,
): LetterGroupReturnCantFinish {
  const depthMm = prev.depthMm;
  switch (finishType) {
    case "same_as_face":
    case "white_aluminum":
    case "black_aluminum":
    case "mirror_silver":
    case "standard_aluminum":
    case "none":
      return {
        finishType,
        depthMm,
        notes: prev.notes,
      };
    case "oracal_wrapped":
      return {
        finishType,
        depthMm,
        materialCode: prev.finishType === "oracal_wrapped" ? prev.materialCode ?? "651" : "651",
        colorCode: prev.finishType === "oracal_wrapped" ? prev.colorCode : undefined,
        colorName: prev.finishType === "oracal_wrapped" ? prev.colorName : undefined,
        notes: prev.notes,
      };
    case "ral_paint":
      return {
        finishType,
        depthMm,
        materialCode: "RAL",
        colorCode: prev.finishType === "ral_paint" ? prev.colorCode : undefined,
        colorName: prev.finishType === "ral_paint" ? prev.colorName : undefined,
        notes: prev.notes,
      };
    case "gold_aluminum":
      return {
        finishType: "gold_aluminum" as LetterGroupReturnFinishType,
        depthMm,
        materialCode: "gold",
        notes: prev.notes,
      };
  }
}

export function isKnownRegistryColor(
  system: "RAL" | "ORACAL",
  code: string | undefined,
  series?: "651" | "8500",
): boolean {
  const trimmed = code?.trim();
  if (!trimmed) return false;
  return lookupColorRegistryItem(system, trimmed, series).status === "found";
}

export function isCustomReturnDepth(depthMm: number | undefined): boolean {
  if (depthMm == null || !Number.isFinite(depthMm)) return false;
  return !(ALLOWED_RETURN_DEPTH_MM as readonly number[]).includes(depthMm);
}

export { ALLOWED_RETURN_DEPTH_MM };