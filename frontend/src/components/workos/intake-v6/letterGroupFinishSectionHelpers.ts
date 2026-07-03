import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";
import {
  letterGroupToReturnCant,
  patchLetterGroupFromReturnCant,
} from "@/lib/intakeV6/intakeV6ReturnCantBridge";

export function patchLetterGroupFinishes(
  groups: IntakeV6LetterGroupFinish[],
  groupKey: string,
  patch: Partial<IntakeV6LetterGroupFinish>,
): IntakeV6LetterGroupFinish[] {
  return groups.map((group) =>
    group.group_key === groupKey ? { ...group, ...patch, confirmed: false } : group,
  );
}

export function copyFirstCantSettingsToAllGroups(
  groups: IntakeV6LetterGroupFinish[],
): IntakeV6LetterGroupFinish[] {
  if (groups.length === 0) return groups;
  const template = patchLetterGroupFromReturnCant(letterGroupToReturnCant(groups[0]!));
  return groups.map((group) => ({
    ...group,
    ...template,
    confirmed: false,
  }));
}
