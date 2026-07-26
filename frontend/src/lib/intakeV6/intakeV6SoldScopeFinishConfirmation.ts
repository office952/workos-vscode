import type { IntakeV4ArtworkFinish } from "./intakeV4ArtworkFinish";
import type { IntakeV4LetterGroupFinish } from "./intakeV4LetterGroups";
import { faceFinishNeedsColorPicker } from "./intakeV6FaceFinishOptions";
import { resolveIntakeV6ReturnFinishUiOption } from "./intakeV6ReturnFinishOptions";
import type { SoldModuleCode } from "./intakeV6OfferScopeState";
import { normalizeSoldModules } from "./intakeV6OfferScopeState";
import type { SoldScopeFieldVisibility } from "./intakeV6SoldScopeVisibility";

export function soldModulesRemoved(
  previous: readonly SoldModuleCode[],
  next: readonly SoldModuleCode[],
): SoldModuleCode[] {
  const nextSet = new Set(normalizeSoldModules(next));
  return normalizeSoldModules(previous).filter((code) => !nextSet.has(code));
}

export function invalidateFinishConfirmationsForDeselectedModules(params: {
  letterGroups: IntakeV4LetterGroupFinish[];
  artworkFinishes: IntakeV4ArtworkFinish[];
  finishSetupConfirmed?: boolean;
  deselectedModules: readonly SoldModuleCode[];
}): {
  letterGroups: IntakeV4LetterGroupFinish[];
  artworkFinishes: IntakeV4ArtworkFinish[];
  finishSetupConfirmed: boolean;
} {
  const deselected = new Set(params.deselectedModules);
  let letterGroups = params.letterGroups;
  let artworkFinishes = params.artworkFinishes;
  let finishSetupConfirmed = params.finishSetupConfirmed === true;

  if (deselected.size === 0) {
    return { letterGroups, artworkFinishes, finishSetupConfirmed };
  }

  if (deselected.has("FACE") || deselected.has("RETURN-CANT")) {
    letterGroups = letterGroups.map((group) =>
      group.confirmed ? { ...group, confirmed: false } : group,
    );
  }

  if (deselected.has("RETURN-CANT")) {
    artworkFinishes = artworkFinishes.map((row) =>
      row.confirmed ? { ...row, confirmed: false } : row,
    );
  }

  if (deselected.has("FACE") || deselected.has("RETURN-CANT") || deselected.has("BACK")) {
    finishSetupConfirmed = false;
  }

  return { letterGroups, artworkFinishes, finishSetupConfirmed };
}

export function isLetterGroupProductConfiguredForScope(
  group: IntakeV4LetterGroupFinish,
  visibility: SoldScopeFieldVisibility,
): boolean {
  if (visibility.face) {
    if (faceFinishNeedsColorPicker(group.face_finish_type) && !group.face_oracal_code?.trim()) {
      return false;
    }
  }

  if (visibility.returnCant) {
    const ui = resolveIntakeV6ReturnFinishUiOption(group.return_finish_type);
    if ((ui === "ral_paint" || ui === "oracal_wrapped") && !group.return_oracal_code?.trim()) {
      return false;
    }
    if (!group.return_finish_type?.trim()) return false;
    if (group.return_depth_mm == null || group.return_depth_mm <= 0) return false;
  }

  return true;
}

export function isArtworkFinishProductConfiguredForScope(
  row: IntakeV4ArtworkFinish,
  visibility: SoldScopeFieldVisibility,
): boolean {
  if (!visibility.face && !visibility.returnCant) {
    return true;
  }

  if (visibility.face) {
    const execution = String(row.execution_type ?? "").trim();
    if (!execution || execution === "needs_decision") return false;
  }

  if (visibility.returnCant) {
    if (row.return_depth_mm == null || row.return_depth_mm <= 0) return false;
  }

  return true;
}

export function countIncompleteLetterGroupsForScope(
  groups: readonly IntakeV4LetterGroupFinish[],
  visibility: SoldScopeFieldVisibility,
): number {
  if (!visibility.face && !visibility.returnCant) {
    return 0;
  }
  return groups.filter((group) => !isLetterGroupProductConfiguredForScope(group, visibility)).length;
}

export function countIncompleteArtworkFinishesForScope(
  rows: readonly IntakeV4ArtworkFinish[],
  visibility: SoldScopeFieldVisibility,
): number {
  if (!visibility.face && !visibility.returnCant) {
    return 0;
  }
  return rows.filter((row) => !isArtworkFinishProductConfiguredForScope(row, visibility)).length;
}
