/**
 * Letters SISTEM LED — structure-step material association.
 */

export function isLettersLedStructureComponent(component: {
  type: string;
  component_id: string;
  name: string;
}): boolean {
  if (component.type === "ELECTRIC_LED" || component.type === "ELECTRIC_PSU") {
    return true;
  }
  const key = `${component.component_id} ${component.name}`
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
  if (
    key.includes("finisaj") ||
    key.includes("finish") ||
    key.includes("fata") ||
    key.includes("face") ||
    key.includes("volum") ||
    key.includes("lateral") ||
    key.includes("sablon")
  ) {
    return false;
  }
  if (
    (key.includes("spate") || key.includes("capac") || key.includes("forex")) &&
    !key.includes("led") &&
    !key.includes("ilumin")
  ) {
    return false;
  }
  return (
    key.includes("led") ||
    key.includes("ilumin") ||
    key.includes("psu") ||
    key.includes("sursa")
  );
}
