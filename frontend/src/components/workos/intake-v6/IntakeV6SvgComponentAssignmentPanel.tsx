/**
 * Compact read-only summary of Product System SVG bindings.
 * Primary assignment UI lives on layer / Contur suport cards — not here.
 */

import { useMemo } from "react";
import type { SvgBindableComponent } from "@/lib/api";
import {
  LEGACY_INTAKE_SVG_ROLE_ADAPTER,
  ownerFacingComponentProductLabel,
  readSvgComponentBindings,
} from "@/lib/intakeV6/svgComponentBindings";
import { v6 } from "./atoms/intakeV6Presentation";

type Props = {
  templateCode: string;
  bindables: SvgBindableComponent[];
  finishSetup: Record<string, unknown> | null | undefined;
  loadError?: string | null;
  usingLegacyFallback?: boolean;
};

export default function IntakeV6SvgComponentAssignmentPanel({
  templateCode,
  bindables,
  finishSetup,
  loadError = null,
  usingLegacyFallback = false,
}: Props) {
  const bindings = useMemo(() => readSvgComponentBindings(finishSetup), [finishSetup]);
  const confirmed = bindings.filter((b) => b.status === "CONFIRMED").length;
  const activeBindables = bindables.filter((c) => {
    const bound = bindings.find((b) => b.component_template_code === c.component_template_code);
    return Boolean(bound && bound.selected_geometry.layer_ids.length + bound.selected_geometry.element_ids.length > 0);
  });

  return (
    <section
      className="rounded border border-wo-border-strong/60 bg-wo-surface-inset/30 px-2.5 py-2"
      data-testid="intake-v6-svg-component-assignment"
      data-variant="summary"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-[11px] font-medium text-slate-300">Rezumat asocieri produs</p>
        <p className="text-[10px] text-slate-500" data-testid="intake-v6-svg-binding-summary-count">
          {confirmed}/{bindings.length || 0} confirmate · {bindables.length} disponibile din Product
          System
        </p>
      </div>
      <p className={`${v6.helper} mt-0.5 text-[10px]`}>
        Asocierea se face pe cardurile de geometrie de mai sus. Template:{" "}
        <span className="font-mono text-slate-500">{templateCode}</span>
      </p>

      {loadError ? (
        <p
          className="mt-1.5 rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[10px] text-amber-100"
          data-testid="intake-v6-svg-bindable-load-error"
        >
          {loadError}
          {usingLegacyFallback ? (
            <span className="mt-0.5 block text-amber-200/80">
              Fallback citire: {LEGACY_INTAKE_SVG_ROLE_ADAPTER} (fără ACP hardcodat).
            </span>
          ) : null}
        </p>
      ) : null}

      {activeBindables.length > 0 ? (
        <ul className="mt-1.5 space-y-0.5 text-[10px] text-slate-400" data-testid="intake-v6-svg-bindable-list">
          {activeBindables.map((c) => {
            const bound = bindings.find((b) => b.component_template_code === c.component_template_code);
            return (
              <li key={c.component_template_code} data-testid={`intake-v6-bindable-${c.component_template_code}`}>
                {ownerFacingComponentProductLabel(c)}
                {bound ? ` · ${bound.status}` : ""}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="mt-1 text-[10px] text-slate-500">Nicio componentă activă încă.</p>
      )}
    </section>
  );
}
