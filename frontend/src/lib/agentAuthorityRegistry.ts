// ============================================================
// Agent Authority Registry — derived from canonical registry
// Canonical source: src/canonical/agent_authority_registry.json
// Canonical doc:    docs/canonical/canonical__agent_authority_map.md
// ============================================================
//
// This module is the ONLY place that bridges the canonical JSON
// registry into the frontend. It adds UI-only presentation fields
// (color, icon) that are NOT part of the canonical business data.
//
// DO NOT add new agents here. Add them to the JSON registry and
// extend the UI_STYLE map below with a matching id.

import registry from "@/canonical/agent_authority_registry.json";

export interface CanonicalAgent {
  id: string;
  label: string;
  domain: string;
  description: string;
  authority: string[];
  noAuthority: string[];
  escalatesWhen: string[];
  owner: string;
  sourceOfTruth: string;
}

export interface AgentRegistry {
  canonicalSource: string;
  version: string;
  updatedAt: string;
  agents: CanonicalAgent[];
}

// UI-only presentation metadata (color + icon). These are NOT canonical.
const UI_STYLE: Record<string, { color: string; icon: string; fullName: string }> = {
  nucleu: { color: "text-amber-400", icon: "⚖️", fullName: "WorkOS - Nucleu" },
  contracts: { color: "text-blue-400", icon: "📋", fullName: "WorkOS - Contracte și Integrare" },
  costing: { color: "text-cyan-400", icon: "💰", fullName: "WorkOS - Costing OC Inventar" },
  ui_ux: { color: "text-purple-400", icon: "🎨", fullName: "WorkOS - UI UX" },
  implementation: { color: "text-emerald-400", icon: "⚙️", fullName: "WorkOS - Implementare" },
  qa: { color: "text-orange-400", icon: "🔍", fullName: "WorkOS - QA Alignment" },
  external: { color: "text-rose-400", icon: "🔌", fullName: "WorkOS - Soluții Externe" },
};

const typedRegistry = registry as AgentRegistry;

/**
 * Frontend-shaped agents array, derived 1:1 from the canonical JSON registry.
 * Preserves the existing Agent interface consumed by Governance.tsx while
 * exposing `owner` and `sourceOfTruth` for discrete display in the UI cards.
 */
const frontendAgents = typedRegistry.agents.map((a) => {
  const ui = UI_STYLE[a.id] || { color: "text-slate-300", icon: "🧩", fullName: a.label };
  return {
    id: a.id,
    name: ui.fullName,
    shortName: a.label,
    role: a.description,
    authority: a.authority,
    noAuthority: a.noAuthority,
    escalatesWhen: a.escalatesWhen,
    owner: a.owner,
    sourceOfTruth: a.sourceOfTruth,
    color: ui.color,
    icon: ui.icon,
  };
});

export default frontendAgents;
export const canonicalSource = typedRegistry.canonicalSource;
export const registryVersion = typedRegistry.version;