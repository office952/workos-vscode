/**
 * Compact AcmPanel provisional pricing — Configurare (Review) live-calc only.
 * Hidden on Confirm (pas 3); no money in inspector / Blueprint / inventory pages.
 */

import { useState } from "react";
import { AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";
import type { AcmPanelCommercialPreview } from "@/lib/intakeV6/intakeV6PricedQuoteTypes";
import {
  acmPanelPreviewIsVisible,
  formatAcmPanelMmPair,
  formatAcmPanelMoney,
  formatAcmPanelMultiPanelDeductionNote,
  formatAcmPanelPanelCountLabel,
  formatAcmPanelPathSource,
  formatAcmPanelQty,
  prepareAcmPanelPreviewWarnings,
} from "@/lib/intakeV6/acmPanel/acmPanelCommercialPreviewDisplay";

export default function AcmPanelProvisionalPricingBlock({
  preview,
  compact = false,
  variant = "default",
  embedded = false,
}: {
  preview: AcmPanelCommercialPreview | null | undefined;
  compact?: boolean;
  /** Quiet row for offer rail — no Final/Execution badges or long provisional essay. */
  variant?: "default" | "rail";
  /** When parent already shows Panou total, render only expandable line details. */
  embedded?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  if (!acmPanelPreviewIsVisible(preview) || !preview) return null;

  const geom = preview.geometry_summary || {};
  const assemblyLabel = formatAcmPanelMmPair(geom.assembly_width_mm, geom.assembly_height_mm);
  const panelCountLabel = formatAcmPanelPanelCountLabel(
    geom.panel_count,
    geom.assembly_width_mm,
    geom.assembly_height_mm,
  );
  const pathSourceLabel = formatAcmPanelPathSource(
    geom.path_measurement_status,
    geom.path_measurement_source,
  );
  const multiPanelNote = formatAcmPanelMultiPanelDeductionNote(
    geom.panel_count,
    geom.path_measurement_status,
    geom.path_measurement_source,
  );
  const currency = preview.currency || "EUR";
  const warnings = prepareAcmPanelPreviewWarnings(preview.warnings, Boolean(pathSourceLabel));
  const lines = preview.lines || [];
  const isRail = variant === "rail";

  if (isRail) {
    if (embedded && lines.length === 0) {
      return (
        <span
          className="sr-only"
          data-testid="intake-v6-acm-panel-provisional-pricing"
          data-variant="rail"
          data-embedded="true"
        >
          Panou Alucobond {formatAcmPanelMoney(preview.estimated_total, currency)}
        </span>
      );
    }
    return (
      <section
        className={
          embedded
            ? "mt-0.5"
            : "mt-1.5 rounded border border-[#2A3548]/55 bg-[#101827]/40 px-2 py-1.5"
        }
        data-testid="intake-v6-acm-panel-provisional-pricing"
        data-variant="rail"
        data-embedded={embedded ? "true" : "false"}
        data-status={preview.status || "unknown"}
        data-final-eligible={preview.final_eligibility ? "true" : "false"}
        data-offer-eligible={preview.offer_eligibility ? "true" : "false"}
        data-execution-eligible={preview.execution_eligibility ? "true" : "false"}
        data-path-source={geom.path_measurement_status || geom.path_measurement_source || "unknown"}
        data-panel-count={panelCountLabel ?? "none"}
      >
        {!embedded ? (
          <header className="flex items-baseline justify-between gap-2">
            <div className="min-w-0">
              <h3
                className="text-[11px] font-medium text-slate-200"
                data-testid="intake-v6-acm-panel-provisional-header"
              >
                Panou Alucobond
              </h3>
              <p
                className="mt-0.5 text-[10px] leading-snug text-slate-500"
                data-testid="intake-v6-acm-panel-provisional-summary"
              >
                Estimare internă
                {assemblyLabel ? ` · ${assemblyLabel}` : ""}
                {panelCountLabel ? ` · ${panelCountLabel}` : ""}
              </p>
            </div>
            <span
              className="shrink-0 text-[12px] font-semibold tabular-nums text-slate-100"
              data-testid="intake-v6-acm-panel-provisional-total"
            >
              {formatAcmPanelMoney(preview.estimated_total, currency)}
            </span>
          </header>
        ) : (
          <span className="sr-only" data-testid="intake-v6-acm-panel-provisional-header">
            Panou Alucobond
          </span>
        )}
        {lines.length > 0 ? (
          <div className={embedded ? "" : "mt-1"}>
            <button
              type="button"
              className="inline-flex items-center gap-0.5 text-[10px] text-slate-400 hover:text-slate-200"
              data-testid="intake-v6-acm-panel-breakdown-toggle"
              aria-expanded={expanded}
              onClick={() => setExpanded((v) => !v)}
            >
              {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              Detalii panou ({lines.length})
            </button>
            {expanded ? (
              <ul className="mt-1 space-y-1" data-testid="intake-v6-acm-panel-breakdown-lines">
                {lines.map((line) => (
                  <li
                    key={String(line.code)}
                    className="flex items-baseline justify-between gap-2 border-t border-[#243044]/40 pt-1 text-[10px]"
                    data-testid={`intake-v6-acm-panel-line-${line.code}`}
                    data-provisional="true"
                  >
                    <span className="min-w-0 text-slate-300">{line.label || line.code}</span>
                    <span className="shrink-0 tabular-nums text-slate-200">
                      {formatAcmPanelMoney(line.amount, currency)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
        {embedded ? (
          <span className="sr-only" data-testid="intake-v6-acm-panel-provisional-total">
            {formatAcmPanelMoney(preview.estimated_total, currency)}
          </span>
        ) : null}
      </section>
    );
  }

  return (
    <section
      className={
        compact
          ? "mt-2 rounded border border-amber-500/20 bg-amber-500/[0.04] px-2 py-1.5"
          : "mt-2.5 rounded-md border border-amber-500/25 bg-amber-500/[0.05] px-2.5 py-2"
      }
      data-testid="intake-v6-acm-panel-provisional-pricing"
      data-status={preview.status || "unknown"}
      data-final-eligible={preview.final_eligibility ? "true" : "false"}
      data-offer-eligible={preview.offer_eligibility ? "true" : "false"}
      data-execution-eligible={preview.execution_eligibility ? "true" : "false"}
      data-path-source={geom.path_measurement_status || geom.path_measurement_source || "unknown"}
      data-panel-count={panelCountLabel ?? "none"}
    >
      <header className="flex items-start gap-1.5">
        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-300/90" aria-hidden />
        <div className="min-w-0 flex-1">
          <h3
            className="text-[11px] font-semibold text-amber-100/95"
            data-testid="intake-v6-acm-panel-provisional-header"
          >
            Estimare provizorie — panou Alucobond
          </h3>
          <p
            className="mt-0.5 text-[10px] leading-snug text-slate-400"
            data-testid="intake-v6-acm-panel-provisional-summary"
          >
            Calcul bazat pe:
            {assemblyLabel ? ` ansamblu ${assemblyLabel}` : " ansamblu"}
            {panelCountLabel ? ` · ${panelCountLabel}` : ""}
            {" · rate din registrul de prețuri"}
          </p>
        </div>
        <span
          className="shrink-0 text-[12px] font-semibold tabular-nums text-amber-50"
          data-testid="intake-v6-acm-panel-provisional-total"
        >
          {formatAcmPanelMoney(preview.estimated_total, currency)}
        </span>
      </header>

      {geom.face_area_m2 != null ? (
        <p
          className="mt-1 text-[10px] tabular-nums text-slate-300"
          data-testid="intake-v6-acm-panel-face-area"
        >
          Arie față: {formatAcmPanelQty(geom.face_area_m2, "mp")}
          {geom.cut_length_m != null
            ? ` · Debitare: ${formatAcmPanelQty(geom.cut_length_m, "ml")}`
            : " · Debitare: indisponibil"}
          {geom.fold_length_m != null
            ? ` · V-groove: ${formatAcmPanelQty(geom.fold_length_m, "ml")}`
            : " · V-groove: indisponibil"}
        </p>
      ) : null}

      {pathSourceLabel ? (
        <p className="mt-1 text-[10px] text-slate-400" data-testid="intake-v6-acm-panel-path-source">
          {pathSourceLabel}
          {multiPanelNote ? ` · ${multiPanelNote}` : ""}
        </p>
      ) : null}

      {(geom.v_groove_l1_ml != null || geom.v_groove_l2_ml != null) && !compact ? (
        <p
          className="mt-0.5 text-[10px] tabular-nums text-slate-500"
          data-testid="intake-v6-acm-panel-vgroove-split"
        >
          V L1: {formatAcmPanelQty(geom.v_groove_l1_ml, "ml")}
          {" · "}
          V L2: {formatAcmPanelQty(geom.v_groove_l2_ml, "ml")}
          {" · "}
          V total: {formatAcmPanelQty(geom.v_groove_total_ml ?? geom.fold_length_m, "ml")}
        </p>
      ) : null}

      <p
        className="mt-1.5 text-[10px] leading-snug text-amber-100/80"
        data-testid="intake-v6-acm-panel-provisional-warning-copy"
      >
        Preț estimativ pentru panou — nu e ofertă fermă. Confirmă panoul Alucobond (pliuri, L1/L2) ca
        cantitățile CUT/V să rămână coerente.
        {geom.path_measurement_status === "proxy_rectangular"
          ? " Cantitățile CUT/V sunt din proxy rectangular, nu din trasee măsurate."
          : ""}
        {geom.path_measurement_status === "commercial_deduced" ||
        geom.path_measurement_status === "commercial_deduced_with_assumptions"
          ? " Cantitățile CUT/V vin din deducere comercială; DXF măsurat e opțional."
          : ""}
        {geom.path_measurement_status === "unavailable"
          ? " Cantitățile CUT/V lipsesc pentru configurația curentă."
          : ""}
      </p>

      {warnings.length > 0 ? (
        <ul className="mt-1.5 space-y-0.5" data-testid="intake-v6-acm-panel-provisional-warnings">
          {warnings.slice(0, compact ? 3 : 6).map((w) => (
            <li key={w} className="text-[10px] text-amber-200/85">
              · {w}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mt-1.5 flex flex-wrap gap-1.5" data-testid="intake-v6-acm-panel-eligibility-badges">
        <span className="rounded border border-slate-600/50 px-1.5 py-0.5 text-[9px] text-slate-400">
          Final: {preview.final_eligibility ? "eligibil" : "indisponibil"}
        </span>
        <span className="rounded border border-slate-600/50 px-1.5 py-0.5 text-[9px] text-slate-400">
          Ofertă fermă: {preview.offer_eligibility ? "eligibilă" : "indisponibilă"}
        </span>
        <span className="rounded border border-slate-600/50 px-1.5 py-0.5 text-[9px] text-slate-400">
          Execution: {preview.execution_eligibility ? "permis" : "blocat"}
        </span>
      </div>

      {lines.length > 0 ? (
        <div className="mt-1.5">
          <button
            type="button"
            className="inline-flex items-center gap-0.5 text-[10px] text-slate-300 hover:text-slate-100"
            data-testid="intake-v6-acm-panel-breakdown-toggle"
            aria-expanded={expanded}
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            Detalii linii panou ({lines.length})
          </button>
          {expanded ? (
            <ul className="mt-1 space-y-1" data-testid="intake-v6-acm-panel-breakdown-lines">
              {lines.map((line) => (
                <li
                  key={String(line.code)}
                  className="flex items-baseline justify-between gap-2 border-t border-[#243044]/40 pt-1 text-[10px]"
                  data-testid={`intake-v6-acm-panel-line-${line.code}`}
                  data-provisional="true"
                >
                  <span className="min-w-0 text-slate-300">
                    <span className="font-medium text-slate-200">{line.label || line.code}</span>
                    <span className="ml-1 tabular-nums text-slate-500">
                      {formatAcmPanelQty(line.quantity, line.unit)}
                      {line.rate != null
                        ? ` · ${formatAcmPanelMoney(line.rate, currency)}/${line.unit || ""}`
                        : ""}
                      {String(line.code) === "acm_boxed_assembly" &&
                      line.amount != null &&
                      line.rate != null &&
                      line.quantity != null &&
                      Number.isFinite(line.amount) &&
                      Number.isFinite(line.rate) &&
                      Number.isFinite(line.quantity) &&
                      line.amount > line.rate * line.quantity + 0.01
                        ? ` · min. ${formatAcmPanelMoney(line.amount, currency)}/produs`
                        : ""}
                    </span>
                  </span>
                  <span className="shrink-0 tabular-nums text-slate-200">
                    {formatAcmPanelMoney(line.amount, currency)}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
