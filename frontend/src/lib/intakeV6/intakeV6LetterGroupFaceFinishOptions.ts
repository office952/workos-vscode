import { INTAKE_V6_FACE_FINISH_OPTIONS } from "./intakeV6FaceFinishOptions";

/** Allowed face finish values for volumetric letter groups (Review Față literei). */
export const INTAKE_V6_LETTER_GROUP_FACE_FINISH_VALUES = [
  "none",
  "oracal_641",
  "oracal_651",
  "oracal_8500",
  "print_laminate",
] as const;

const DISALLOWED_LETTER_GROUP_FACE_FINISH = new Set([
  "printed_vinyl",
  "printed_laminated_vinyl",
  "colored_plexiglas",
]);

export function isDisallowedLetterGroupFaceFinish(value: string): boolean {
  return DISALLOWED_LETTER_GROUP_FACE_FINISH.has(value.trim().toLowerCase());
}

/** Letter-group face dropdown — excludes print vinyl options from template contract. */
export function resolveLetterGroupFaceFinishOptions(
  templateOptions?: readonly { value: string; label: string }[],
): readonly { value: string; label: string }[] {
  const labelByValue = new Map<string, string>();
  for (const opt of INTAKE_V6_FACE_FINISH_OPTIONS) {
    labelByValue.set(opt.value, opt.label);
  }
  if (templateOptions) {
    for (const opt of templateOptions) {
      if (opt.value === "printed_laminated_vinyl") {
        // Prefer canonical face option label (Printat / Laminat); do not invent from legacy wording.
        continue;
      }
      if (!isDisallowedLetterGroupFaceFinish(opt.value)) {
        labelByValue.set(opt.value, opt.label);
      }
    }
  }
  return INTAKE_V6_LETTER_GROUP_FACE_FINISH_VALUES.map((value) => ({
    value,
    label: labelByValue.get(value) ?? value,
  }));
}
