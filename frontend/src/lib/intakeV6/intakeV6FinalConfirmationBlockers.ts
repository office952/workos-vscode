/**
 * Operator-facing final-confirmation blockers for Page 2 sticky summary.
 * Maps known gates to Romanian actions + tab/section targets (no raw enums in UI).
 */

import type { IntakeV6ReviewTabId } from "./intakeV6ProductPlugin";
import { isProductCompositionConfirmed } from "./intakeV6Readiness";
import { readSegmentedBackground } from "./segmentedBackground";
import { readSegmentedElectrical } from "./segmentedElectrical";

export type FinalConfirmationBlocker = {
  id: string;
  severity: "blocker" | "warning";
  /** Short section label, e.g. "Compoziție" */
  section: string;
  message: string;
  action: string;
  tabId: IntakeV6ReviewTabId | "layers" | null;
  focusTarget: string | null;
};

export function buildFinalConfirmationBlockers(input: {
  payload: Record<string, unknown> | undefined;
  finish: Record<string, unknown> | null | undefined;
}): FinalConfirmationBlocker[] {
  const out: FinalConfirmationBlocker[] = [];
  const payload = input.payload;
  const finish = input.finish ?? (payload?.finish_setup as Record<string, unknown> | undefined);

  if (!isProductCompositionConfirmed(payload)) {
    out.push({
      id: "composition",
      severity: "blocker",
      section: "Compoziție",
      message: "Compoziția produsului nu este confirmată.",
      action: "Confirmă compoziția produsului deasupra taburilor.",
      tabId: null,
      focusTarget: "intake-v6-confirm-product-composition",
    });
  }

  const segmented = readSegmentedBackground(finish);
  if (segmented) {
    const status = String(segmented.status || "").toUpperCase();
    const validation = (segmented.validation as { blockers?: Array<{ code?: string; message?: string }> } | undefined)
      ?.blockers;
    const hasCutout = Array.isArray(segmented.element_bindings)
      ? segmented.element_bindings.some(
          (b) =>
            String((b as { construction_type?: string }).construction_type || "").includes("CUTOUT") ||
            String((b as { binding_kind?: string }).binding_kind || "").includes("CUTOUT"),
        )
      : false;
    const hasInsert = Array.isArray(segmented.element_bindings)
      ? segmented.element_bindings.some(
          (b) =>
            String((b as { construction_type?: string }).construction_type || "").includes("INSERT") ||
            String((b as { binding_kind?: string }).binding_kind || "").includes("INSERT"),
        )
      : false;

    if (status === "PROPOSED") {
      out.push({
        id: "segmented-proposed",
        severity: "warning",
        section: "Fundal și carcasă",
        message: "Există o propunere de fundal din mai multe panouri.",
        action: "Confirmă sau respinge ansamblul în tab-ul Montaj.",
        tabId: "montaj",
        focusTarget: "intake-v6-segmented-background-panel",
      });
    }

    if (Array.isArray(validation) && validation.length > 0 && status !== "REJECTED") {
      for (const blocker of validation.slice(0, 3)) {
        const code = String(blocker.code || "");
        const msg = String(blocker.message || "").trim();
        const isCutout = /CUTOUT|decupaj/i.test(`${code} ${msg}`) || hasCutout;
        const isInsert = /INSERT|insert/i.test(`${code} ${msg}`) || hasInsert;
        out.push({
          id: `seg-val-${code || msg.slice(0, 24)}`,
          severity: "blocker",
          section: "Fundal și carcasă",
          message: isCutout
            ? "Un decupaj trece peste îmbinare și blochează confirmarea."
            : isInsert
              ? "Un insert trece peste îmbinare și blochează confirmarea."
              : msg || "Există un blocaj pe ansamblul multi-panou.",
          action: "Rezolvă condiția în clusterul Fundal și carcasă (Montaj).",
          tabId: "montaj",
          focusTarget: "intake-v6-segmented-confirm-blockers",
        });
      }
    }

    if (status === "CONFIRMED") {
      const elec = readSegmentedElectrical(segmented as unknown as Record<string, unknown>);
      if (elec && String(elec.status || "").toUpperCase() !== "CONFIRMED") {
        const unresolved = (elec.panels || []).some(
          (p) => String(p.supply_mode || "").toUpperCase() === "UNCONFIRMED",
        );
        if (unresolved || String(elec.status || "").toUpperCase() === "DRAFT") {
          out.push({
            id: "elec-draft",
            severity: "warning",
            section: "Fundal și carcasă",
            message: "Alimentarea 220V pe panouri nu este confirmată.",
            action: "Completează și confirmă alimentarea în Montaj → Fundal și carcasă.",
            tabId: "montaj",
            focusTarget: "intake-v6-segmented-electrical-panel",
          });
        }
      }
    }
  }

  return out;
}

export function mergeFinalBlockersIntoBannerIssues(
  finalBlockers: FinalConfirmationBlocker[],
): Array<{
  id: string;
  severity: "blocker" | "warning";
  code: string | null;
  message: string;
  action: string | null;
  focusTarget: string | null;
  tabId?: IntakeV6ReviewTabId | "layers" | null;
}> {
  return finalBlockers.map((b) => ({
    id: `final-${b.id}`,
    severity: b.severity,
    code: null,
    message: `${b.section}: ${b.message}`,
    action: b.action,
    focusTarget: b.focusTarget,
    tabId: b.tabId,
  }));
}
