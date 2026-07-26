/**
 * Letters CAPAC SPATE — structure-step material association (Forex 10 mm).
 */

export function isLettersBackForexStructureComponent(component: {
  type: string;
  component_id: string;
  name: string;
}): boolean {
  const key = `${component.component_id} ${component.name}`
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
  if (
    key.includes("sablon") ||
    key.includes("template") ||
    key.includes("montaj") ||
    key.includes("led") ||
    key.includes("finisaj") ||
    key.includes("finish") ||
    key.includes("fata") ||
    key.includes("face") ||
    key.includes("volum") ||
    key.includes("lateral")
  ) {
    return false;
  }
  return (
    key.includes("spate") ||
    key.includes("capac") ||
    key.includes("back") ||
    key.includes("forex") ||
    key.includes("backing")
  );
}
