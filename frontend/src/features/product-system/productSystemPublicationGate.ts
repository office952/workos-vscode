/**
 * Presentation fail-closed gate for Publică.
 * Publication GET alone is not sufficient when readiness is BLOCKED
 * or not yet checked — UI never enables publish in those cases.
 */

import type { ProductTemplatePublicationState } from "@/api/productTemplatePublication";
import { formatPublicationBlocker, humanTemplateName } from "./productSystemAdminDisplay";

const PUBLISHABLE_VERDICTS = new Set([
  "STATIC_READY",
  "STATIC_READY_WITH_WARNINGS",
  "RUNTIME_READY",
]);

export type ReadinessGateInput = {
  verdict?: string | null;
  e2eReady?: boolean | null;
  knownConflicts?: string[] | null;
  findings?: Array<{ blocking?: boolean; message?: string; code?: string }> | null;
};

export type PublishUiGate = {
  publishEnabled: boolean;
  disabledReasonRo: string | null;
  primaryBlockerRo: string | null;
  secondaryCode: string | null;
  readinessBlocks: boolean;
  publicationBlocks: boolean;
};

function aluminiuFromFindings(
  findings: ReadinessGateInput["findings"],
): { primary: string; secondary?: string } | null {
  if (!findings?.length) return null;
  for (const finding of findings) {
    if (!finding.blocking) continue;
    const message = finding.message ?? "";
    const codeMatch = message.match(/TPL-VOLUM-ALUMINIU[_A-Z0-9]*/i);
    if (codeMatch || /aluminiu/i.test(message)) {
      const code = codeMatch?.[0] ?? "TPL-VOLUM-ALUMINIU_v1";
      return {
        primary: `${humanTemplateName(code)} inactiv (copil obligatoriu)`,
        secondary: code,
      };
    }
  }
  return null;
}

function primaryFromPublicationBlockers(
  blockers: string[],
): { primary: string; secondary?: string } | null {
  if (!blockers.length) return null;
  const aluminiu = blockers.find((b) => /ALUMINIU/i.test(b));
  const raw = aluminiu ?? blockers[0];
  const display = formatPublicationBlocker(raw);
  return { primary: display.primary, secondary: display.secondary };
}

/**
 * Fail-closed: Publică enabled only when publication allows AND readiness
 * is known-publishable. Missing readiness ⇒ disabled.
 */
export function resolvePublishUiGate(
  publication: ProductTemplatePublicationState | null | undefined,
  readiness?: ReadinessGateInput | null,
): PublishUiGate {
  if (!publication) {
    return {
      publishEnabled: false,
      disabledReasonRo: "Starea de publicare nu este disponibilă.",
      primaryBlockerRo: null,
      secondaryCode: null,
      readinessBlocks: true,
      publicationBlocks: true,
    };
  }

  const publicationBlocks =
    !publication.publish_allowed || publication.publish_blockers.length > 0;

  const verdict = (readiness?.verdict ?? publication.last_e2e_verdict ?? "").trim();
  const hasReadinessSignal = Boolean(verdict) || readiness?.e2eReady != null;
  const readinessBlocks =
    !hasReadinessSignal ||
    readiness?.e2eReady === false ||
    (verdict.length > 0 && !PUBLISHABLE_VERDICTS.has(verdict)) ||
    Boolean(readiness?.knownConflicts?.includes("required_inactive_child"));

  const aluminiu = aluminiuFromFindings(readiness?.findings);
  const fromPub = primaryFromPublicationBlockers(publication.publish_blockers);

  let primaryBlockerRo: string | null = null;
  let secondaryCode: string | null = null;
  if (aluminiu) {
    primaryBlockerRo = aluminiu.primary;
    secondaryCode = aluminiu.secondary ?? null;
  } else if (fromPub) {
    primaryBlockerRo = fromPub.primary;
    secondaryCode = fromPub.secondary ?? null;
  } else if (readinessBlocks && verdict) {
    primaryBlockerRo = `Pregătire E2E: ${verdict}`;
  } else if (readinessBlocks && !hasReadinessSignal) {
    primaryBlockerRo = "Verifică traseul produsului (Pregătire E2E) înainte de publicare";
  }

  const publishEnabled = !publicationBlocks && !readinessBlocks;

  let disabledReasonRo: string | null = null;
  if (!publishEnabled) {
    disabledReasonRo = primaryBlockerRo
      ? `Publică dezactivat: ${primaryBlockerRo}`
      : "Publică dezactivat — publicarea este blocată.";
  }

  return {
    publishEnabled,
    disabledReasonRo,
    primaryBlockerRo,
    secondaryCode,
    readinessBlocks,
    publicationBlocks,
  };
}

/** Whether the Publish action button must render disabled. */
export function isPublishActionDisabled(
  publication: ProductTemplatePublicationState | null | undefined,
  readiness?: ReadinessGateInput | null,
  loading = false,
): boolean {
  if (loading) return true;
  return !resolvePublishUiGate(publication, readiness).publishEnabled;
}
