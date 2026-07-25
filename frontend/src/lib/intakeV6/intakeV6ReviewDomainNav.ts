import type { LucideIcon } from "lucide-react";
import { Boxes, Layers, Lightbulb, Wrench } from "lucide-react";
import type { IntakeV6ReviewTabDefinition, IntakeV6ReviewTabId } from "./intakeV6ProductPlugin";

/**
 * Operator-facing workbench domains on Review (Pas 2).
 * Panou/carcasă and Montaj comercial both map to the canonical `montaj` tab;
 * UI splits authority without changing modular contract tab ids.
 */
export type IntakeV6ReviewDomainId =
  | "finisaje"
  | "iluminare"
  | "panou_carcasa"
  | "montaj_comercial";

export type IntakeV6ReviewDomainDefinition = {
  id: IntakeV6ReviewDomainId;
  label: string;
  hint: string;
  icon: LucideIcon;
  mapsToTab: IntakeV6ReviewTabId;
};

const PANOU_DOMAIN: IntakeV6ReviewDomainDefinition = {
  id: "panou_carcasa",
  label: "Panou / carcasă",
  hint: "Geometrie · suport · L1/L2",
  icon: Boxes,
  mapsToTab: "montaj",
};

const MONTAJ_COMERCIAL_DOMAIN: IntakeV6ReviewDomainDefinition = {
  id: "montaj_comercial",
  label: "Montaj comercial",
  hint: "Scope · șablon · șantier",
  icon: Wrench,
  mapsToTab: "montaj",
};

const FALLBACK_ICON: Record<IntakeV6ReviewTabId, LucideIcon> = {
  finisaje: Layers,
  iluminare: Lightbulb,
  montaj: Wrench,
};

/**
 * Expand canonical review tabs into workbench domains.
 * Replaces a single `montaj` tab with Panou/carcasă + Montaj comercial.
 */
export function expandReviewTabsToDomains(
  tabs: IntakeV6ReviewTabDefinition[],
): IntakeV6ReviewDomainDefinition[] {
  const out: IntakeV6ReviewDomainDefinition[] = [];
  for (const tab of tabs) {
    if (tab.id === "montaj") {
      out.push(PANOU_DOMAIN, MONTAJ_COMERCIAL_DOMAIN);
      continue;
    }
    out.push({
      id: tab.id,
      label: tab.label,
      hint: tab.hint,
      icon: tab.icon ?? FALLBACK_ICON[tab.id],
      mapsToTab: tab.id,
    });
  }
  return out;
}

export function resolveReviewDomainFromTab(
  tab: IntakeV6ReviewTabId,
  montajDomain: "panou_carcasa" | "montaj_comercial",
  domains: IntakeV6ReviewDomainDefinition[],
): IntakeV6ReviewDomainId {
  if (tab === "montaj") {
    const preferred = domains.find((d) => d.id === montajDomain);
    if (preferred) return preferred.id;
    const firstMontaj = domains.find((d) => d.mapsToTab === "montaj");
    if (firstMontaj) return firstMontaj.id;
  }
  const match = domains.find((d) => d.id === tab);
  if (match) return match.id;
  return domains[0]?.id ?? "finisaje";
}

export function domainSelectionToTabState(
  domainId: IntakeV6ReviewDomainId,
): {
  tab: IntakeV6ReviewTabId;
  montajDomain: "panou_carcasa" | "montaj_comercial";
} {
  if (domainId === "panou_carcasa") {
    return { tab: "montaj", montajDomain: "panou_carcasa" };
  }
  if (domainId === "montaj_comercial") {
    return { tab: "montaj", montajDomain: "montaj_comercial" };
  }
  return { tab: domainId, montajDomain: "panou_carcasa" };
}
