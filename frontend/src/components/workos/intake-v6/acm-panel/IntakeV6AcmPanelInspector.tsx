/**
 * AcmPanel operator inspector — progressive disclosure sections.
 * Consumes uiReadModel; writes only via operatorPatch callbacks.
 */

import { useEffect, useRef, useState, type ReactNode } from "react";
import IntakeV6SegmentedBackgroundPanel from "../IntakeV6SegmentedBackgroundPanel";
import {
  authorityHintForField,
  type AcmPanelIssue,
  type AcmPanelUiReadModel,
} from "@/lib/intakeV6/acmPanel/uiReadModel";
import type { AcmOperatorFieldKey } from "@/lib/intakeV6/acmPanel/operatorPatch";
import type { SegmentedBackground } from "@/lib/intakeV6/segmentedBackground";

export type AcmPanelInspectorActions = {
  onUpdateField: (field: AcmOperatorFieldKey, value: number | boolean | 1 | 2 | null) => void;
  onConfirmField: (fieldKeys: string[]) => void;
  onConfirmConstruction: () => void;
  onConfirmTechnical: () => void;
  onConfirmRelation: (relationId: string) => void;
  onSegmentedPatch: (patch: { segmented_background: SegmentedBackground }) => void;
};

function Section({
  id,
  title,
  open,
  onToggle,
  status,
  children,
}: {
  id: string;
  title: string;
  open: boolean;
  onToggle: () => void;
  status?: string;
  children: ReactNode;
}) {
  return (
    <div
      className="rounded border border-[#2A3548]/60 bg-[#0A0F1A]/35"
      data-testid={`intake-v6-acm-section-${id}`}
      data-open={open ? "true" : "false"}
    >
      <button
        type="button"
        className="flex w-full items-center gap-2 px-2.5 py-2 text-left"
        onClick={onToggle}
        aria-expanded={open}
      >
        <span className="text-[12px] font-semibold text-slate-100">{title}</span>
        {status ? (
          <span className="rounded border border-amber-500/25 px-1.5 py-0.5 text-[10px] text-amber-200">
            {status}
          </span>
        ) : null}
        <span className="ml-auto text-[10px] text-slate-500">{open ? "▾" : "▸"}</span>
      </button>
      {open ? <div className="border-t border-[#2A3548]/50 px-2.5 py-2">{children}</div> : null}
    </div>
  );
}

function AuthorityHint({ model, fieldKey }: { model: AcmPanelUiReadModel; fieldKey: string }) {
  const hint = authorityHintForField(model, fieldKey);
  return (
    <span className="text-[10px] text-slate-500" data-testid={`intake-v6-acm-authority-${fieldKey}`}>
      {hint.label}
    </span>
  );
}

export default function IntakeV6AcmPanelInspector({
  model,
  finishSetup,
  actions,
  focusIssue,
  onFocusConsumed,
}: {
  model: AcmPanelUiReadModel;
  finishSetup: Record<string, unknown> | null | undefined;
  actions: AcmPanelInspectorActions;
  focusIssue?: AcmPanelIssue | null;
  onFocusConsumed?: () => void;
}) {
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    summary: true,
    geometry: false,
    construction: false,
    segments: false,
    material: false,
    structure: false,
    relations: false,
    technical: false,
  });
  const rootRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!focusIssue) return;
    setOpenSections((prev) => ({ ...prev, [focusIssue.sectionId]: true, summary: true }));
    const t = window.setTimeout(() => {
      if (focusIssue.fieldTestId) {
        const el = document.querySelector(
          `[data-testid="${focusIssue.fieldTestId}"]`,
        ) as HTMLElement | null;
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          el.focus?.();
          el.classList.add("ring-2", "ring-amber-400/60");
          window.setTimeout(() => el.classList.remove("ring-2", "ring-amber-400/60"), 1600);
        }
      }
      onFocusConsumed?.();
    }, 50);
    return () => window.clearTimeout(t);
  }, [focusIssue, onFocusConsumed]);

  if (!model.exists || !model.instance) {
    return (
      <section
        className="rounded border border-[#2A3548]/50 px-3 py-4 text-[12px] text-slate-400"
        data-testid="intake-v6-acm-panel-inspector"
      >
        Niciun Panou Alucobond instanțiat pe acest workspace.
      </section>
    );
  }

  const inst = model.instance;
  const cfg = inst.configuration;
  const toggle = (id: string) =>
    setOpenSections((prev) => ({ ...prev, [id]: !prev[id] }));

  return (
    <section
      ref={rootRef}
      className="space-y-2"
      data-testid="intake-v6-acm-panel-inspector"
    >
      <Section
        id="summary"
        title="Rezumat"
        open={openSections.summary}
        onToggle={() => toggle("summary")}
        status={model.primaryStatus.label}
      >
        <div className="space-y-1 text-[11px] text-slate-300" data-testid="intake-v6-acm-summary">
          <p className="text-[13px] font-semibold text-slate-100">{model.label}</p>
          <p data-testid="intake-v6-acm-summary-association">
            Asociere: {model.association.label}
          </p>
          <p>Tehnic: {model.technical.label}</p>
          <p>Compoziție instanță: {model.composition.label}</p>
          <p>Dimensiuni: {model.dimensionsSummary ?? "—"}</p>
          <p>Segmente: {model.segmentCount} ({model.segmentedLabel})</p>
          {model.unresolvedConfirmations.length ? (
            <p className="text-amber-200">
              Nerezolvat: {model.unresolvedConfirmations.join(" · ")}
            </p>
          ) : null}
          {model.activeCapabilities.length ? (
            <p className="text-slate-500">
              Capabilități active: {model.activeCapabilities.join(", ")}
            </p>
          ) : null}
        </div>
      </Section>

      <Section
        id="geometry"
        title="Geometrie"
        open={openSections.geometry}
        onToggle={() => toggle("geometry")}
        status={authorityHintForField(model, "panel_geometry").label}
      >
        <div className="grid gap-2 sm:grid-cols-2">
          <label className="block text-[11px]">
            <span className="text-slate-500">Lățime (mm)</span>
            <input
              type="number"
              className="mt-0.5 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[11px]"
              value={inst.geometry.width_mm ?? ""}
              data-testid="intake-v6-acm-field-panel_geometry"
              onChange={(e) =>
                actions.onUpdateField("panel_width_mm", Number(e.target.value))
              }
            />
            <AuthorityHint model={model} fieldKey="panel_geometry" />
          </label>
          <label className="block text-[11px]">
            <span className="text-slate-500">Înălțime (mm)</span>
            <input
              type="number"
              className="mt-0.5 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[11px]"
              value={inst.geometry.height_mm ?? ""}
              onChange={(e) =>
                actions.onUpdateField("panel_height_mm", Number(e.target.value))
              }
            />
          </label>
        </div>
        <p className="mt-2 text-[10px] text-slate-500">
          Sursă: SVG / detected · unități mm
          {inst.geometry.bbox
            ? ` · bbox ${inst.geometry.bbox.width.toFixed(2)}×${inst.geometry.bbox.height.toFixed(2)}`
            : ""}
        </p>
        <button
          type="button"
          className="mt-2 rounded border border-emerald-500/30 px-2 py-1 text-[11px] text-emerald-200"
          onClick={() => actions.onConfirmField(["panel_geometry"])}
        >
          Confirmă geometria
        </button>
      </Section>

      <Section
        id="construction"
        title="Construcție"
        open={openSections.construction}
        onToggle={() => toggle("construction")}
        status={model.technical.label}
      >
        <p className="mb-2 text-[10px] text-slate-500">
          Tip:{" "}
          {cfg.fold_count === 2
            ? "față + perete + buză"
            : cfg.fold_count === 1
              ? "față + perete"
              : "nespecificat"}
        </p>
        <div className="grid gap-2 sm:grid-cols-2">
          {(
            [
              ["acm_thickness_mm", "Grosime ACM", cfg.acm_thickness_mm],
              ["l1_mm", "Perete / întoarcere", cfg.l1_mm],
              ["l2_mm", "Buză interioară", cfg.l2_mm],
              ["fold_count", "Fold count", cfg.fold_count],
            ] as const
          ).map(([key, label, value]) => (
            <label key={key} className="block text-[11px]">
              <span className="text-slate-500">{label}</span>
              <input
                type="number"
                className="mt-0.5 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[11px]"
                value={value ?? ""}
                data-testid={`intake-v6-acm-field-${key}`}
                onChange={(e) =>
                  actions.onUpdateField(
                    key as AcmOperatorFieldKey,
                    key === "fold_count"
                      ? (Number(e.target.value) as 1 | 2)
                      : Number(e.target.value),
                  )
                }
              />
              <AuthorityHint model={model} fieldKey={key} />
            </label>
          ))}
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded border border-amber-500/35 px-2 py-1 text-[11px] text-amber-100"
            data-testid="intake-v6-acm-confirm-construction"
            onClick={() => actions.onConfirmConstruction()}
          >
            Confirmă valorile din construcție
          </button>
          <button
            type="button"
            className="rounded border border-emerald-500/35 px-2 py-1 text-[11px] text-emerald-100"
            data-testid="intake-v6-acm-confirm-technical"
            onClick={() => actions.onConfirmTechnical()}
          >
            Confirmă configurația tehnică
          </button>
        </div>
        <p className="mt-2 text-[10px] text-slate-500">
          Propunerile din catalog nu sunt confirmate până la acțiunea explicită. Compoziția produsului
          se confirmă separat.
        </p>
      </Section>

      <Section
        id="segments"
        title="Segmente"
        open={openSections.segments}
        onToggle={() => toggle("segments")}
        status={model.segmentedLabel}
      >
        <IntakeV6SegmentedBackgroundPanel
          finish={finishSetup}
          onPatch={actions.onSegmentedPatch}
        />
      </Section>

      <Section
        id="material"
        title="Material și finisaj"
        open={openSections.material}
        onToggle={() => toggle("material")}
      >
        <p className="text-[11px] text-slate-400">
          Grosime ACM: {cfg.acm_thickness_mm ?? "—"} mm ·{" "}
          <AuthorityHint model={model} fieldKey="acm_thickness_mm" />
        </p>
        <p className="mt-1 text-[10px] text-slate-500">
          Module culoare / folie / vopsire — fără inventare; extensibile ulterior pe capability.
        </p>
      </Section>

      <Section
        id="structure"
        title="Structură și montaj"
        open={openSections.structure}
        onToggle={() => toggle("structure")}
      >
        <p className="text-[11px] text-slate-300">
          Cadru interior: {cfg.internal_frame_enabled ? "activ" : "inactiv"}
        </p>
        <p className="mt-1 text-[10px] text-slate-500">
          Montajul pe perete / structură se confirmă explicit ca relație operațională — nu din
          geometrie.
        </p>
        {model.mountingRelations.length === 0 ? (
          <p className="mt-1 text-[11px] text-slate-500">Nicio relație mounts_on / attached_to_structure.</p>
        ) : (
          <ul className="mt-1 space-y-1">
            {model.mountingRelations.map((rel) => (
              <li
                key={rel.relation_id}
                className="flex items-center justify-between gap-2 text-[11px] text-slate-300"
                data-testid={`intake-v6-acm-relation-${rel.relation_id}`}
              >
                <span>
                  {rel.relation_type} · {rel.status}
                </span>
                {rel.status !== "confirmed" ? (
                  <button
                    type="button"
                    className="rounded border border-emerald-500/30 px-1.5 py-0.5 text-[10px] text-emerald-200"
                    onClick={() => actions.onConfirmRelation(rel.relation_id)}
                  >
                    Confirmă
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section
        id="relations"
        title="Relații"
        open={openSections.relations}
        onToggle={() => toggle("relations")}
      >
        <p className="text-[10px] font-semibold uppercase text-slate-500">Geometrice</p>
        <ul className="mt-1 space-y-1 text-[11px] text-slate-300">
          {model.geometryRelations.length ? (
            model.geometryRelations.map((rel) => (
              <li key={rel.relation_id}>
                {rel.relation_type}: {rel.from_component_ref} → {rel.to_component_ref} (
                {rel.status})
              </li>
            ))
          ) : (
            <li className="text-slate-500">Nicio relație geometrică.</li>
          )}
        </ul>
        <p className="mt-2 text-[10px] font-semibold uppercase text-slate-500">
          Operaționale / montaj
        </p>
        <p className="text-[10px] text-slate-500">
          mounts_on / attached_to_structure — doar confirmare operator (vezi Structură și montaj).
        </p>
      </Section>

      <Section
        id="technical"
        title="Detalii tehnice"
        open={openSections.technical}
        onToggle={() => toggle("technical")}
      >
        <pre
          className="overflow-x-auto whitespace-pre-wrap font-mono text-[10px] text-slate-500"
          data-testid="intake-v6-acm-tech"
        >
          {JSON.stringify(
            {
              component_instance_id: inst.component_instance_id,
              template: inst.component_template_code,
              source: model.source,
              adapter: inst.intake_geometry_role_adapter,
              statuses: {
                role: inst.role_status,
                association: inst.association_status,
                technical: inst.technical_configuration_status,
                composition: inst.composition_status,
              },
              contour_id: inst.geometry.contour_id,
              geometry_hash: inst.geometry.geometry_hash,
              svg_source_hash: inst.svg_source_hash,
              inconsistency: model.inconsistencyNotes,
            },
            null,
            2,
          )}
        </pre>
      </Section>
    </section>
  );
}
