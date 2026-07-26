/**
 * Letters VOLUM ALUMINIU — structure-step material association (4 widths).
 * Parallel to FACE ↔ plexiglas: this step ↔ profil aluminiu Al 0.6 mm.
 */

export function isLettersVolumeAluminumStructureComponent(component: {
  type: string;
  component_id: string;
  name: string;
}): boolean {
  const key = `${component.component_id} ${component.name}`
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
  if (key.includes("lateral") || key.includes("volum") || key.includes("return") || key.includes("cant")) {
    // Exclude FINISAJ / face finish rows that mention cant in finish sense only.
    if (key.includes("finis") || key.includes("face") || key.includes("fata") || key.includes("vizual")) {
      return false;
    }
    return true;
  }
  if (key.includes("profil") && (key.includes("liter") || key.includes("alu"))) {
    return true;
  }
  return false;
}
