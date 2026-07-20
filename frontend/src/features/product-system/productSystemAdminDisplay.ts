/**
 * Admin-facing display helpers for Product System UI polish.
 * Human name primary; technical codes secondary. No authority changes.
 */

const TEMPLATE_HUMAN_NAMES: Record<string, string> = {
  "TPL-VOLUMETRIC-LETTERS_v2": "Litere volumetrice",
  "TPL-VOLUMETRIC-LETTERS": "Litere volumetrice",
  "TPL-VOLUM-ALUMINIU_v1": "Aluminiu (volumetric)",
  "TPL-VOLUM-ALUMINIU": "Aluminiu (volumetric)",
  "TPL-ACM-CASSETTED-PANEL": "Panou ACM casetat",
  "TPL-VOLUMETRIC-LOGO": "Logo volumetric",
};

export function humanTemplateName(code: string | null | undefined): string {
  if (!code) return "—";
  const trimmed = code.trim();
  return TEMPLATE_HUMAN_NAMES[trimmed] ?? trimmed.replace(/^TPL-/, "").replace(/_/g, " ");
}

export type BlockerDisplay = {
  primary: string;
  secondary?: string;
  raw: string;
};

/** Map machine publish/readiness blockers → operator-readable lines. */
export function formatPublicationBlocker(raw: string): BlockerDisplay {
  const value = raw.trim();
  if (value.startsWith("known_conflict:")) {
    const code = value.slice("known_conflict:".length);
    return {
      primary: `${humanTemplateName(code)} — conflict activ (ex. copil inactiv)`,
      secondary: code,
      raw: value,
    };
  }
  if (value.startsWith("last_e2e_verdict_not_publishable:")) {
    const verdict = value.slice("last_e2e_verdict_not_publishable:".length);
    return {
      primary: `Ultimul verdict E2E nu permite publicarea (${verdict})`,
      secondary: value,
      raw: value,
    };
  }
  if (value.startsWith("readiness_verdict_")) {
    const verdict = value.slice("readiness_verdict_".length);
    return {
      primary: `Verificarea E2E blochează publicarea (${verdict})`,
      secondary: value,
      raw: value,
    };
  }
  if (value.startsWith("blocking_findings:")) {
    const n = value.slice("blocking_findings:".length);
    return {
      primary: `${n} findings blochează publicarea`,
      secondary: value,
      raw: value,
    };
  }
  if (value === "template_inactive") {
    return { primary: "Șablonul este inactiv în catalog (DB)", secondary: value, raw: value };
  }
  // Heuristic: template-looking tokens inside free text
  const tplMatch = value.match(/TPL-[A-Z0-9_-]+/i);
  if (tplMatch) {
    const code = tplMatch[0];
    return {
      primary: value.replace(code, humanTemplateName(code)),
      secondary: code,
      raw: value,
    };
  }
  return { primary: value, raw: value };
}

export function formatReadinessFindingMessage(message: string): {
  primary: string;
  secondary?: string;
} {
  const tplMatch = message.match(/TPL-[A-Z0-9_-]+/i);
  if (!tplMatch) return { primary: message };
  const code = tplMatch[0];
  return {
    primary: message.replace(code, humanTemplateName(code)),
    secondary: code,
  };
}

export const RELATION_TYPE_LABELS_RO: Record<string, string> = {
  required_child: "Copil obligatoriu",
  optional_addon: "Addon opțional",
  conditional_child: "Copil condiționat",
  composition_link: "Legătură compoziție",
};

export function relationTypeLabelRo(value: string): string {
  return RELATION_TYPE_LABELS_RO[value] ?? value;
}
