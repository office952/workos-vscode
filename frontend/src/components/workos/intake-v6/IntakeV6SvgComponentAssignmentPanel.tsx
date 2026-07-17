/**
 * Product System–driven SVG component associations for Intake V6 Step 1.
 * Options come from template-availability.svg_bindable_components — not hardcoded ACP.
 */

import { useEffect, useMemo, useState } from "react";
import { productTemplateAvailabilityApi, type SvgBindableComponent } from "@/lib/api";
import type { LayerRoleConfirmation, SvgAnalysisReport } from "@/lib/svgAnalyzer";
import {
  filterBindableForUi,
  LEGACY_INTAKE_SVG_ROLE_ADAPTER,
  letterBinding,
  logoBinding,
  ownerGeometryLabel,
  readSvgComponentBindings,
  upsertBinding,
  type SvgComponentBinding,
} from "@/lib/intakeV6/svgComponentBindings";
import { v6 } from "./atoms/intakeV6Presentation";
import IntakeV6AlucobondContourPanel from "./IntakeV6AlucobondContourPanel";

type Props = {
  templateCode: string;
  report: SvgAnalysisReport;
  confirmation: LayerRoleConfirmation | null;
  finishSetup: Record<string, unknown> | null | undefined;
  svgSourceHash: string | null | undefined;
  disabled?: boolean;
  onSelectedContourIdChange?: (contourId: string | null) => void;
  onPersistFinish: (patch: {
    svg_support_selection?: Record<string, unknown> | null;
    svg_component_bindings?: SvgComponentBinding[];
    mounting_solution?: Record<string, unknown> | null;
    power_supply_service_corner?: string | null;
  }) => Promise<void> | void;
};

export default function IntakeV6SvgComponentAssignmentPanel({
  templateCode,
  report,
  confirmation,
  finishSetup,
  svgSourceHash,
  disabled = false,
  onSelectedContourIdChange,
  onPersistFinish,
}: Props) {
  const [bindables, setBindables] = useState<SvgBindableComponent[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [usingLegacy, setUsingLegacy] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoadError(null);
    setUsingLegacy(false);
    productTemplateAvailabilityApi
      .list({ include_runtime_modules: true, include_archived: false })
      .then((res) => {
        if (cancelled) return;
        const item = res.items.find((row) => row.template_code === templateCode);
        const list = filterBindableForUi(item?.svg_bindable_components ?? []);
        if (!item || list.length === 0) {
          setBindables([]);
          setLoadError("Product System nu a returnat componente SVG-bindable pentru template.");
          setUsingLegacy(true);
          return;
        }
        setBindables(list);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setBindables([]);
        setUsingLegacy(true);
        setLoadError(err instanceof Error ? err.message : "Nu s-a putut încărca availability.");
      });
    return () => {
      cancelled = true;
    };
  }, [templateCode]);

  const bindings = useMemo(() => readSvgComponentBindings(finishSetup), [finishSetup]);
  const byCode = useMemo(
    () => Object.fromEntries(bindings.map((b) => [b.component_template_code, b])),
    [bindings],
  );

  const lettersComp = bindables.find((c) =>
    c.accepted_geometry_roles?.includes("LETTER_VECTOR_SET"),
  );
  const logoComp = bindables.find((c) => c.accepted_geometry_roles?.includes("LOGO_VECTOR_SET"));
  const supportComp = bindables.find((c) =>
    c.accepted_geometry_roles?.includes("SUPPORT_CONTOUR"),
  );

  const syncLayerBindings = async () => {
    if (!confirmation || !lettersComp) {
      return;
    }
    setBusy(true);
    try {
      const letterLayers = confirmation.layers
        .filter((l) => l.confirmedRole === "face" && l.state !== "ignored")
        .map((l) => l.layerKey);
      const logoLayers = confirmation.layers
        .filter(
          (l) =>
            (l.confirmedRole === "printed_artwork" || l.confirmedRole === "logo") &&
            l.state !== "ignored",
        )
        .map((l) => l.layerKey);

      let next = [...bindings];
      next = upsertBinding(
        next,
        letterBinding({
          layerIds: letterLayers,
          sourceSvgHash: svgSourceHash ?? null,
          componentCode: lettersComp.component_template_code,
          selectionMode: lettersComp.selection_mode,
        }),
      );
      if (logoComp && logoLayers.length) {
        next = upsertBinding(
          next,
          logoBinding({
            layerIds: logoLayers,
            sourceSvgHash: svgSourceHash ?? null,
            componentCode: logoComp.component_template_code,
            selectionMode: logoComp.selection_mode,
          }),
        );
      } else {
        next = next.filter((b) => b.geometry_role !== "LOGO_VECTOR_SET");
      }
      await onPersistFinish({ svg_component_bindings: next });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section
      className={`${v6.cardCompact} space-y-3`}
      data-testid="intake-v6-svg-component-assignment"
    >
      <div>
        <h3 className={v6.sectionTitle}>Asocieri produs</h3>
        <p className={v6.helper}>
          Componentele vin din Product System (<code className="text-[10px]">{templateCode}</code>).
          Geometria se asociază componentei reale — nu unui Product Template paralel.
        </p>
      </div>

      {loadError ? (
        <p
          className="rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1.5 text-[11px] text-amber-100"
          data-testid="intake-v6-svg-bindable-load-error"
        >
          {loadError}
          {usingLegacy ? (
            <span className="mt-1 block text-amber-200/80">
              Fallback citire: {LEGACY_INTAKE_SVG_ROLE_ADAPTER} (fără ACP hardcodat).
            </span>
          ) : null}
        </p>
      ) : null}

      {bindables.length > 0 ? (
        <ul className="space-y-2" data-testid="intake-v6-svg-bindable-list">
          {bindables.map((c) => {
            const bound = byCode[c.component_template_code];
            const roles = (c.accepted_geometry_roles ?? [])
              .map((r) => ownerGeometryLabel(r))
              .join(", ");
            return (
              <li
                key={c.component_template_code}
                className="rounded border border-[#2A3548] bg-[#0A0F1A]/60 px-2 py-1.5 text-[11px]"
                data-testid={`intake-v6-bindable-${c.component_template_code}`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-medium text-slate-100">{c.owner_label}</span>
                  <span className="text-[10px] text-slate-500">
                    {c.required ? "Obligatoriu" : "Optional"}
                    {c.active_by_default ? "" : " · inactiv implicit"}
                  </span>
                </div>
                <div className="mt-0.5 font-mono text-[10px] text-slate-500">
                  {c.component_template_code}
                </div>
                <div className="mt-0.5 text-[10px] text-slate-400">
                  {roles || "fără rol SVG"} · {c.selection_mode} · {c.cardinality}
                </div>
                {c.guards?.length ? (
                  <div className="mt-0.5 text-[10px] text-amber-200/80">Guard: {c.guards.join(", ")}</div>
                ) : null}
                <div className="mt-1 text-[10px] text-cyan-200/90">
                  {bound
                    ? `Asociere: ${bound.status}${
                        bound.selected_geometry.layer_ids.length
                          ? ` · ${bound.selected_geometry.layer_ids.length} layere`
                          : ""
                      }${
                        bound.selected_geometry.element_ids.length
                          ? ` · ${bound.selected_geometry.element_ids[0]}`
                          : ""
                      }`
                    : "Neasociat"}
                </div>
              </li>
            );
          })}
        </ul>
      ) : null}

      {lettersComp ? (
        <div className="space-y-2 border-t border-[#2A3548]/80 pt-3">
          <p className="text-[11px] text-slate-400">
            Vector litere / Vector logo: confirmă rolurile pe layere, apoi sincronizează asocierea
            componentei.
          </p>
          <button
            type="button"
            disabled={disabled || busy || !confirmation}
            className={v6.btnSecondary}
            data-testid="intake-v6-sync-layer-component-bindings"
            onClick={() => void syncLayerBindings()}
          >
            Confirmă asocierea litere/logo → componente Product System
          </button>
        </div>
      ) : null}

      {supportComp ? (
        <div className="space-y-2 border-t border-[#2A3548]/80 pt-3">
          <h4 className="text-[12px] font-semibold text-slate-200">
            Contur suport → {supportComp.owner_label}
          </h4>
          <p className="text-[11px] text-slate-500">
            Selection mode: {supportComp.selection_mode} · cardinalitate {supportComp.cardinality}
          </p>
          <IntakeV6AlucobondContourPanel
            report={report}
            finishSetup={finishSetup}
            svgSourceHash={svgSourceHash}
            disabled={disabled || busy}
            onSelectedContourIdChange={onSelectedContourIdChange}
            onPersist={onPersistFinish}
          />
        </div>
      ) : report.closedContourCandidates ? (
        <p className="text-[11px] text-slate-500">
          Contururi detectate, dar Product System nu expune componentă SUPPORT_CONTOUR pentru acest
          template (inactive isolation).
        </p>
      ) : null}
    </section>
  );
}
