import type { LetterGroupReturnCantFinish, LetterGroupReturnFinishType } from "./intakeV6ReturnFinishModel";
import { buildReturnForFinishType } from "./intakeV6ReturnFinishModel";

export type IntakeV6ReturnFinishUiOption =
  | "white"
  | "black"
  | "gold"
  | "silver"
  | "ral_paint"
  | "oracal_wrapped";

export const INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE = "white_aluminum";
export const INTAKE_V6_CANT_VOLUM_LABEL = "Cant / volum";
export const INTAKE_V6_CANT_VOLUM_LABEL_LOWER = "cant / volum";
export const INTAKE_V6_CANT_VOLUM_LETTERS_LABEL = "Cant / volum litere";
export const INTAKE_V6_CANT_VOLUM_ARTWORK_LABEL = "Cant / volum artwork";

export const INTAKE_V6_RETURN_FINISH_UI_OPTIONS: {
  value: IntakeV6ReturnFinishUiOption;
  label: string;
}[] = [
  { value: "white", label: "Alb" },
  { value: "black", label: "Negru" },
  { value: "gold", label: "Auriu" },
  { value: "silver", label: "Argintiu" },
  { value: "ral_paint", label: "Vopsit RAL" },
  { value: "oracal_wrapped", label: "Oracal 651" },
];

const UI_TO_INTERNAL: Record<IntakeV6ReturnFinishUiOption, LetterGroupReturnFinishType | "gold_aluminum"> = {
  white: "white_aluminum",
  black: "black_aluminum",
  gold: "gold_aluminum",
  silver: "mirror_silver",
  ral_paint: "ral_paint",
  oracal_wrapped: "oracal_wrapped",
};

const INTERNAL_TO_UI: Record<string, IntakeV6ReturnFinishUiOption | null> = {
  white_aluminum: "white",
  black_aluminum: "black",
  gold_aluminum: "gold",
  mirror_silver: "silver",
  standard_aluminum: "silver",
  ral_paint: "ral_paint",
  painted: "ral_paint",
  paint: "ral_paint",
  oracal_wrapped: "oracal_wrapped",
  oracal_651: "oracal_wrapped",
  vinyl: "oracal_wrapped",
};

export function intakeV6ReturnFinishUiToInternal(
  option: IntakeV6ReturnFinishUiOption,
): LetterGroupReturnFinishType | "gold_aluminum" {
  return UI_TO_INTERNAL[option];
}

export function intakeV6InternalReturnFinishToUi(
  finishType: string | null | undefined,
): IntakeV6ReturnFinishUiOption | null {
  const token = String(finishType ?? "").trim().toLowerCase();
  if (!token) return null;
  return INTERNAL_TO_UI[token] ?? null;
}

export function buildIntakeV6ReturnCantForUiOption(
  option: IntakeV6ReturnFinishUiOption,
  prev: LetterGroupReturnCantFinish,
): LetterGroupReturnCantFinish {
  const internal = intakeV6ReturnFinishUiToInternal(option);
  const next = buildReturnForFinishType(internal as LetterGroupReturnFinishType, prev);
  if (option === "oracal_wrapped") {
    return {
      ...next,
      finishType: "oracal_wrapped",
      materialCode: "651",
    };
  }
  if (option === "gold") {
    return {
      ...next,
      finishType: "gold_aluminum" as LetterGroupReturnFinishType,
      materialCode: "gold",
    };
  }
  return next;
}

export function formatIntakeV6ReturnFinishLabel(args: {
  finishType: string | null | undefined;
  colorCode?: string | null;
  colorName?: string | null;
  materialCode?: string | null;
}): string {
  const token = String(args.finishType ?? "").trim().toLowerCase();
  const ui = intakeV6InternalReturnFinishToUi(token);

  if (ui === "white") return "Alb";
  if (ui === "black") return "Negru";
  if (ui === "gold" || token === "gold_aluminum") return "Auriu";
  if (ui === "silver" || token === "standard_aluminum") return "Argintiu";
  if (ui === "ral_paint" || token === "painted" || token === "ral_paint") {
    const code = args.colorCode?.trim();
    if (code) {
      const name = args.colorName?.trim();
      return name ? `Vopsit RAL ${code} — ${name}` : `Vopsit RAL ${code}`;
    }
    return "Vopsit RAL";
  }
  if (ui === "oracal_wrapped" || token === "oracal_wrapped") {
    const name = args.colorName?.trim();
    const code = args.colorCode?.trim();
    if (name) return `Oracal 651 ${name}`;
    if (code) return `Oracal 651 — ${code}`;
    return "Oracal 651";
  }

  if (token === "same_as_face") return "La fel ca fața (legacy)";
  if (token === "none" || token === "unspecified") return `${INTAKE_V6_CANT_VOLUM_LABEL} nespecificat (legacy)`;
  if (!token) return "—";
  return token.replace(/_/g, " ");
}

export function isIntakeV6LegacyReturnFinish(finishType: string | null | undefined): boolean {
  const token = String(finishType ?? "").trim().toLowerCase();
  return token === "same_as_face" || token === "none" || token === "unspecified";
}

export function resolveIntakeV6ReturnFinishUiOption(
  finishType: string | null | undefined,
): IntakeV6ReturnFinishUiOption {
  const token = String(finishType ?? "").trim().toLowerCase();
  if (!token) return "white";
  return intakeV6InternalReturnFinishToUi(finishType) ?? "silver";
}