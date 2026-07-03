import type { ProductTemplateComponent } from "@/lib/api";

export interface ExplicitConstructionStage {
  code: string;
  label: string;
  componentIndex?: number;
  component_id?: string;
  disabled?: boolean;
}

export interface DerivedConstructionStage {
  code: string;
  label: string;
  chipLabel: string;
  componentIndex: number;
  componentType: ProductTemplateComponent["type"];
}

/**
 * Optional metadata embedded in notes as JSON:
 * { "construction_stages": [{ "code", "label", "component_id"? }] }
 */
export function parseExplicitConstructionStagesFromNotes(
  notes: string | undefined | null
): ExplicitConstructionStage[] | null {
  const trimmed = (notes ?? "").trim();
  if (!trimmed.startsWith("{")) return null;
  try {
    const parsed = JSON.parse(trimmed) as Record<string, unknown>;
    const raw = parsed.construction_stages ?? parsed.production_stages;
    if (!Array.isArray(raw)) return null;
    const stages: ExplicitConstructionStage[] = [];
    for (const item of raw) {
      if (!item || typeof item !== "object") continue;
      const row = item as Record<string, unknown>;
      const code = String(row.code ?? row.id ?? "").trim();
      const label = String(row.label ?? row.name ?? "").trim();
      if (!code || !label) continue;
      stages.push({
        code,
        label,
        component_id:
          typeof row.component_id === "string" ? row.component_id : undefined,
        componentIndex:
          typeof row.componentIndex === "number" ? row.componentIndex : undefined,
        disabled: row.disabled === true,
      });
    }
    return stages.length > 0 ? stages : null;
  } catch {
    return null;
  }
}

/** Short chip label — prefer name before em-dash, uppercased for scanability. */
export function formatConstructionStageChipLabel(label: string): string {
  const short = label.split("—")[0].split(" - ")[0].trim();
  return short.length > 0 ? short.toUpperCase() : label.toUpperCase();
}

export function deriveConstructionStages(
  components: ProductTemplateComponent[],
  options?: {
    explicitStages?: ExplicitConstructionStage[] | null;
    getStageLabel?: (component: ProductTemplateComponent, index: number) => string;
  }
): DerivedConstructionStage[] {
  const getLabel =
    options?.getStageLabel ??
    ((component: ProductTemplateComponent) =>
      component.name.trim() || component.component_id);

  const explicit = options?.explicitStages;
  if (explicit && explicit.length > 0) {
    return explicit
      .filter((stage) => !stage.disabled)
      .map((stage) => {
        const componentIndex =
          stage.componentIndex ??
          components.findIndex((c) => c.component_id === stage.component_id);
        const component =
          componentIndex >= 0 ? components[componentIndex] : undefined;
        if (componentIndex < 0 || !component || component._legacy === true) {
          return null;
        }
        return {
          code: stage.code,
          label: stage.label,
          chipLabel: formatConstructionStageChipLabel(stage.label),
          componentIndex,
          componentType: component.type,
        };
      })
      .filter((stage): stage is DerivedConstructionStage => stage !== null);
  }

  return components
    .map((component, index) => ({ component, index }))
    .filter(({ component }) => component._legacy !== true)
    .map(({ component, index }) => {
      const label = getLabel(component, index);
      return {
        code: component.component_id,
        label,
        chipLabel: formatConstructionStageChipLabel(label),
        componentIndex: index,
        componentType: component.type,
      };
    });
}
