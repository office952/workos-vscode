/**
 * Preserve ACM panel shell when letter/logo binding sync runs.
 * Uses acm_panel_domain_action=preserve — never blind-clear.
 */

import {
  readSvgComponentBindings,
  type SvgComponentBinding,
} from "../svgComponentBindings";
import type { IntakeV6FinishSetup } from "../intakeV6Api";
import type { AcmPanelDomainAction } from "./types";
import { ACM_PANEL_TEMPLATE_CODE } from "./types";

export function mergeLetterLogoBindingsPreservingAcmPanelDomain(args: {
  letterLogoBindings: SvgComponentBinding[];
  finishSetup: IntakeV6FinishSetup | Record<string, unknown> | null | undefined;
  supportRoleStillConfirmed: boolean;
}): {
  svg_component_bindings: SvgComponentBinding[];
  svg_support_selection?: unknown;
  mounting_solution?: unknown;
  acm_panel_instance?: unknown;
  segmented_background?: unknown;
  acm_panel_domain_action: AcmPanelDomainAction;
} {
  const existing = readSvgComponentBindings(args.finishSetup);
  const acmShell = existing.filter(
    (b) =>
      b.geometry_role === "SUPPORT_CONTOUR" ||
      b.component_template_code === ACM_PANEL_TEMPLATE_CODE,
  );
  const lettersLogos = args.letterLogoBindings.filter(
    (b) => b.geometry_role !== "SUPPORT_CONTOUR",
  );

  if (!args.supportRoleStillConfirmed) {
    return {
      svg_component_bindings: lettersLogos,
      acm_panel_domain_action: "preserve",
    };
  }

  const finish = (args.finishSetup || {}) as Record<string, unknown>;
  return {
    svg_component_bindings: [...lettersLogos, ...acmShell],
    svg_support_selection: finish.svg_support_selection,
    mounting_solution: finish.mounting_solution,
    acm_panel_instance: finish.acm_panel_instance,
    segmented_background: finish.segmented_background,
    acm_panel_domain_action: "preserve",
  };
}
