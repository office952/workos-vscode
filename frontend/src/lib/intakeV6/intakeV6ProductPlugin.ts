import type { LucideIcon } from "lucide-react";
import { Layers, Lightbulb, Wrench } from "lucide-react";

/** Review sub-tabs on the Intake V6 Review step (page 2). */
export type IntakeV6ReviewTabId = "finisaje" | "iluminare" | "montaj";

export interface IntakeV6ReviewTabDefinition {
  id: IntakeV6ReviewTabId;
  label: string;
  hint: string;
  icon: LucideIcon;
  /** Mini-module codes from the modular form contract linked to this tab. */
  moduleCodes: string[];
}

export interface IntakeV6ProductPlugin {
  /** Primary template code (canonical registry key). */
  templateCode: string;
  /** Alternate codes that resolve to this plugin (e.g. legacy without _v2). */
  templateCodeAliases: string[];
  /** Human label for diagnostics and future template picker. */
  displayName: string;
  reviewTabs: IntakeV6ReviewTabDefinition[];
}

const VOLUMETRIC_LETTERS_REVIEW_TABS: IntakeV6ReviewTabDefinition[] = [
  {
    id: "finisaje",
    label: "Finisaje",
    hint: "Față · cant · Vector Logo",
    icon: Layers,
    moduleCodes: ["face", "cant", "artwork"],
  },
  {
    id: "iluminare",
    label: "Iluminare și surse",
    hint: "LED · surse litere",
    icon: Lightbulb,
    moduleCodes: ["led", "backing"],
  },
  {
    id: "montaj",
    label: "Montaj",
    hint: "Fundal · carcasă · site",
    icon: Wrench,
    moduleCodes: ["mounting", "template"],
  },
];

const VOLUMETRIC_LETTERS_PLUGIN: IntakeV6ProductPlugin = {
  templateCode: "TPL-VOLUMETRIC-LETTERS_v2",
  templateCodeAliases: ["TPL-VOLUMETRIC-LETTERS"],
  displayName: "Litere volumetrice",
  reviewTabs: VOLUMETRIC_LETTERS_REVIEW_TABS,
};

/** Registered product plugins keyed by canonical template_code. */
const INTAKE_V6_PRODUCT_PLUGINS: IntakeV6ProductPlugin[] = [VOLUMETRIC_LETTERS_PLUGIN];

const pluginByTemplateCode = new Map<string, IntakeV6ProductPlugin>();

for (const plugin of INTAKE_V6_PRODUCT_PLUGINS) {
  pluginByTemplateCode.set(normalizeTemplateCode(plugin.templateCode), plugin);
  for (const alias of plugin.templateCodeAliases) {
    pluginByTemplateCode.set(normalizeTemplateCode(alias), plugin);
  }
}

function normalizeTemplateCode(code: string): string {
  return code.trim().toUpperCase();
}

/**
 * Resolve the product plugin for a workspace template code.
 * Returns null when the template is unknown — callers fall back to legacy volumetric UI.
 */
export function resolveIntakeV6ProductPlugin(
  templateCode: string | null | undefined,
): IntakeV6ProductPlugin | null {
  const normalized = templateCode?.trim();
  if (!normalized) return null;
  return pluginByTemplateCode.get(normalizeTemplateCode(normalized)) ?? null;
}

/**
 * Review tab definitions for the Review step tab bar.
 * Falls back to the pilot volumetric tabs when no plugin matches.
 */
export function resolveIntakeV6ReviewTabs(
  templateCode: string | null | undefined,
): IntakeV6ReviewTabDefinition[] {
  return resolveIntakeV6ProductPlugin(templateCode)?.reviewTabs ?? VOLUMETRIC_LETTERS_REVIEW_TABS;
}

/** @internal Exposed for tests and future registry tooling. */
export function listIntakeV6ProductPlugins(): readonly IntakeV6ProductPlugin[] {
  return INTAKE_V6_PRODUCT_PLUGINS;
}
