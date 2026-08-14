/**
 * Display copy for CURRENT_WORKOS_FROZEN_AS_REFERENCE on /modules and /governance.
 * Presentation only — not a freeze engine, registry, or status API.
 */

export const WORKOS_REFERENCE_FREEZE_STATUS = "ON" as const;

export const WORKOS_REFERENCE_FREEZE_CODE =
  "CURRENT_WORKOS_FROZEN_AS_REFERENCE = ON";

export const WORKOS_REFERENCE_FREEZE_LABEL_RO = "Referință înghețată";

export const WORKOS_REFERENCE_FREEZE_BODY_RO =
  "Modelul WorkOS curent este referință înghețată. Schimbările de implementare se fac doar prin valuri delimitate, autorizate explicit.";

export const WORKOS_BOUNDED_EXCEPTION_BODY_RO =
  "Modificările de după freeze sunt permise doar prin excepții delimitate, autorizate explicit de owner. Aceste excepții nu reprezintă o dezghețare generală a aplicației.";
