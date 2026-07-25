/**
 * ACM panel-alone composition detection + operator teaching scope.
 * One flag drives capture/UI honesty: what this sold element needs vs VL letter chrome.
 */

import { Wrench } from "lucide-react";
import type { IntakeV6ReviewTabDefinition } from "../intakeV6ProductPlugin";

export function isAcmPanelOnlyComposition(
  payload: Record<string, unknown> | null | undefined,
): boolean {
  if (!payload) return false;
  const recommendation = payload.product_composition_recommendation;
  if (recommendation && typeof recommendation === "object" && !Array.isArray(recommendation)) {
    const ctype = String(
      (recommendation as { composition_type?: unknown }).composition_type ?? "",
    )
      .trim()
      .toLowerCase();
    if (ctype === "support_only" || ctype === "support_only_pending") return true;
  }

  const confirmed = payload.product_composition_confirmed;
  if (!(confirmed && typeof confirmed === "object" && !Array.isArray(confirmed))) return false;
  if ((confirmed as { confirmed?: unknown }).confirmed !== true) return false;
  const items = (confirmed as { items?: unknown }).items;
  if (!Array.isArray(items) || items.length === 0) return false;
  const codes = new Set(
    items
      .filter((it): it is Record<string, unknown> => !!it && typeof it === "object")
      .map((it) => String(it.template_code ?? "").trim())
      .filter(Boolean),
  );
  return codes.size === 1 && codes.has("TPL-ACM-BOXED-MOUNTING-SUPPORT_v1");
}

/** Operator-facing teaching: in-scope vs out-of-scope needs for ACM panel-alone. */
export type AcmPanelOnlyUiScope = {
  isAcmPanelOnly: boolean;
  scopeChipLabelRo: string;
  offerScopeTitleRo: string;
  offerScopeBodyRo: string;
  inScopeNeedsRo: string[];
  outOfScopeNeedsRo: string[];
};

const ACM_PANEL_ONLY_UI_SCOPE: AcmPanelOnlyUiScope = {
  isAcmPanelOnly: true,
  scopeChipLabelRo: "Panou Alucobond casetat · fără litere",
  offerScopeTitleRo: "Scope ofertă — panou ACM",
  offerScopeBodyRo:
    "Oferta vinde panoul Alucobond casetat. Intake cere doar ce ține de panou — nu modulele de litere volumetrice.",
  inScopeNeedsRo: [
    "Geometrie panou (lățime × înălțime)",
    "Construcție casetat (întoarceri, L1/L2, grosime ACM)",
    "Finisaj shell pe panou (dacă e în ofertă)",
    "Cadru interior — opțiune tehnică (neprețuită în CPP)",
  ],
  outOfScopeNeedsRo: [
    "Față / cant litere volumetrice",
    "Adeziv lipire cant pe fețe litere",
    "Plexiglas / LED litere",
    "Finisaje vinil / print litere",
  ],
};

const NOT_ACM_PANEL_ONLY_UI_SCOPE: AcmPanelOnlyUiScope = {
  isAcmPanelOnly: false,
  scopeChipLabelRo: "",
  offerScopeTitleRo: "",
  offerScopeBodyRo: "",
  inScopeNeedsRo: [],
  outOfScopeNeedsRo: [],
};

export function resolveAcmPanelOnlyUiScope(
  payload: Record<string, unknown> | null | undefined,
): AcmPanelOnlyUiScope {
  return isAcmPanelOnlyComposition(payload)
    ? ACM_PANEL_ONLY_UI_SCOPE
    : NOT_ACM_PANEL_ONLY_UI_SCOPE;
}

/** Review tabs for ACM panel-alone — no Față/Cant/LED letter chrome. */
export function acmPanelOnlyReviewTabs(
  base: IntakeV6ReviewTabDefinition[] | null | undefined,
): IntakeV6ReviewTabDefinition[] {
  const montaj = (base ?? []).find((tab) => tab.id === "montaj");
  return [
    {
      id: "montaj",
      label: montaj?.label ?? "Panou ACM",
      hint: "Alucobond casetat · construcție · finisaj shell",
      icon: montaj?.icon ?? Wrench,
      moduleCodes: montaj?.moduleCodes ?? ["mounting", "template"],
    },
  ];
}
