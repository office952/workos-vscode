/**
 * Contur suport geometry card — same interaction model as layer cards.
 * Hosts closed-contour selection + progressive ACP configuration.
 */

import type { SvgBindableComponent } from "@/lib/api";
import type { SvgAnalysisReport } from "@/lib/svgAnalyzer";
import {
  ownerFacingComponentProductLabel,
  ownerGeometryLabel,
  readSvgComponentBindings,
  type SvgComponentBinding,
} from "@/lib/intakeV6/svgComponentBindings";
import { readSvgSupportSelection } from "@/lib/svgAnalyzer";
import IntakeV6AlucobondContourPanel from "./IntakeV6AlucobondContourPanel";

type Props = {
  supportComp: SvgBindableComponent;
  report: SvgAnalysisReport;
  finishSetup: Record<string, unknown> | null | undefined;
  svgSourceHash: string | null | undefined;
  disabled?: boolean;
  onSelectedContourIdChange?: (contourId: string | null) => void;
  onPersist: (patch: {
    svg_support_selection?: Record<string, unknown> | null;
    svg_component_bindings?: SvgComponentBinding[];
    mounting_solution?: Record<string, unknown> | null;
    power_supply_service_corner?: string | null;
  }) => Promise<void> | void;
};

export default function IntakeV6SupportContourGeometryCard({
  supportComp,
  report,
  finishSetup,
  svgSourceHash,
  disabled = false,
  onSelectedContourIdChange,
  onPersist,
}: Props) {
  const cc = report.closedContourCandidates;
  if (!cc || cc.candidate_count === 0) return null;

  const bindings = readSvgComponentBindings(finishSetup);
  const supportBinding = bindings.find(
    (b) => b.component_template_code === supportComp.component_template_code,
  );
  const selection = readSvgSupportSelection(finishSetup ?? undefined);
  const active =
    selection.status === "confirmed" ||
    selection.status === "draft" ||
    selection.status === "reconfirm_required" ||
    Boolean(supportBinding);
  const statusLabel =
    selection.status === "confirmed" && supportBinding?.status === "CONFIRMED"
      ? "Confirmat"
      : selection.status === "reconfirm_required"
        ? "Necesită reconfirmare"
        : active
          ? "Selectat"
          : "Disponibil · inactiv";

  return (
    <article
      className="rounded-md border border-[#2A3548]/80 bg-[#0A0F1A]/40 px-3 py-3 sm:col-span-2 xl:col-span-2"
      data-testid="intake-v6-support-contour-card"
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[12px] font-semibold text-slate-100">
            {ownerGeometryLabel("SUPPORT_CONTOUR")}
          </p>
          <p className="text-[11px] text-slate-500">
            Contur închis detectat · {cc.candidate_count} candidat
            {cc.candidate_count === 1 ? "" : "e"}
          </p>
        </div>
        <span
          className="shrink-0 rounded border border-slate-600/60 px-1.5 py-0.5 text-[10px] text-slate-400"
          data-testid="intake-v6-support-contour-status"
        >
          {statusLabel}
        </span>
      </div>

      <div
        className="mb-2 rounded border border-[#2A3548]/80 bg-[#0A0F1A]/70 px-2 py-1.5"
        data-testid="intake-v6-support-contour-component"
      >
        <p className="text-[10px] uppercase tracking-wide text-slate-500">Componentă produs</p>
        <p className="text-[12px] font-medium text-slate-100">
          {ownerFacingComponentProductLabel(supportComp)}
        </p>
        <p className="mt-0.5 text-[10px] text-slate-400">
          {supportComp.required ? "Obligatoriu" : "Opțional"}
          {!active ? " · disponibil, nu activ" : ""}
        </p>
        <details className="mt-1">
          <summary className="cursor-pointer text-[10px] text-slate-500">Detalii tehnice</summary>
          <p className="mt-0.5 font-mono text-[10px] text-slate-500">
            {supportComp.component_template_code}
          </p>
        </details>
      </div>

      <IntakeV6AlucobondContourPanel
        report={report}
        finishSetup={finishSetup}
        svgSourceHash={svgSourceHash}
        disabled={disabled}
        variant="embedded"
        onSelectedContourIdChange={onSelectedContourIdChange}
        onPersist={onPersist}
      />
    </article>
  );
}
