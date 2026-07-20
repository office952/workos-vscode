/**
 * AcmPanel operator inspector — progressive disclosure sections.
 * Numeric fields use local draft + debounce; confirms combine pending updates into one PUT.
 */

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import IntakeV6SegmentedBackgroundPanel from "../IntakeV6SegmentedBackgroundPanel";
import {
  authorityHintForField,
  type AcmPanelIssue,
  type AcmPanelUiReadModel,
} from "@/lib/intakeV6/acmPanel/uiReadModel";
import {
  buildAcmPanelConfirmActionWithUpdatesPatch,
  buildAcmPanelUpdateFieldsPatch,
} from "@/lib/intakeV6/acmPanel/operatorPatch";
import {
  useAcmPanelOperatorDrafts,
  type AcmPanelOperatorDraftsApi,
} from "@/lib/intakeV6/acmPanel/useAcmPanelOperatorDrafts";
import type { AcmPanelDraftNumericField } from "@/lib/intakeV6/acmPanel/commitSemantics";
import type { AcmPanelFlushResult } from "@/lib/intakeV6/acmPanel/commitSemantics";
import type { SegmentedBackground } from "@/lib/intakeV6/segmentedBackground";
import type { IntakeV6FinishSetup } from "@/lib/intakeV6/intakeV6Api";

export type AcmPanelInspectorActions = {
  onApplyFinishPatch: (patch: Partial<IntakeV6FinishSetup>) => void;
  onSegmentedPatch: (patch: { segmented_background: SegmentedBackground }) => void;
};

export type IntakeV6AcmPanelInspectorHandle = {
  flushAll: () => AcmPanelFlushResult;
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

function sectionForField(field: AcmPanelDraftNumericField): string {
  if (field === "panel_width_mm" || field === "panel_height_mm") return "geometry";
  return "construction";
}

function DraftNumberInput({
  field,
  label,
  drafts,
  model,
  authorityKey,
}: {
  field: AcmPanelDraftNumericField;
  label: string;
  drafts: AcmPanelOperatorDraftsApi;
  model: AcmPanelUiReadModel;
  authorityKey: string;
}) {
  const props = drafts.getFieldProps(field);
  return (
    <label className="block text-[11px]">
      <span className="text-slate-500">{label}</span>
      <input
        type="text"
        inputMode="decimal"
        className={`mt-0.5 w-full rounded border bg-[#0A0F1A] px-2 py-1.5 text-[11px] ${
          props.status === "invalid"
            ? "border-rose-500/50 text-rose-100"
            : "border-[#2A3548] text-slate-100"
        }`}
        value={props.value}
        data-testid={`intake-v6-acm-field-${field}`}
        data-draft-status={props.status}
        onChange={(e) => props.onChange(e.target.value)}
        onBlur={() => props.onBlur()}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            props.onEnter();
          }
        }}
      />
      <AuthorityHint model={model} fieldKey={authorityKey} />
      {props.error ? (
        <p className="mt-0.5 text-[10px] text-rose-300" data-testid={`intake-v6-acm-field-error-${field}`}>
          {props.error}
        </p>
      ) : null}
    </label>
  );
}

const IntakeV6AcmPanelInspector = forwardRef<
  IntakeV6AcmPanelInspectorHandle,
  {
    model: AcmPanelUiReadModel;
    finishSetup: Record<string, unknown> | null | undefined;
    actions: AcmPanelInspectorActions;
    focusIssue?: AcmPanelIssue | null;
    onFocusConsumed?: () => void;
  }
>(function IntakeV6AcmPanelInspector(
  { model, finishSetup, actions, focusIssue, onFocusConsumed },
  ref,
) {
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

  const canonical = useMemo(() => {
    const cfg = model.instance?.configuration;
    const geo = model.instance?.geometry;
    return {
      panel_width_mm: geo?.width_mm,
      panel_height_mm: geo?.height_mm,
      acm_thickness_mm: cfg?.acm_thickness_mm,
      l1_mm: cfg?.l1_mm,
      l2_mm: cfg?.l2_mm,
      fold_count: cfg?.fold_count,
    };
  }, [model.instance]);

  const drafts = useAcmPanelOperatorDrafts({
    canonical,
    onCommitUpdates: (updates) => {
      const patch = buildAcmPanelUpdateFieldsPatch({ finishSetup, updates });
      if (patch) actions.onApplyFinishPatch(patch);
    },
  });

  useImperativeHandle(
    ref,
    () => ({
      flushAll: () => drafts.flushAll(),
    }),
    [drafts],
  );

  const focusInvalid = (field: AcmPanelDraftNumericField) => {
    setOpenSections((prev) => ({
      ...prev,
      [sectionForField(field)]: true,
      summary: true,
    }));
    window.setTimeout(() => {
      const el = document.querySelector(
        `[data-testid="intake-v6-acm-field-${field}"]`,
      ) as HTMLElement | null;
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
      el?.focus?.();
    }, 50);
  };

  const requestSectionToggle = (id: string) => {
    const result = drafts.flushAll();
    if (result.status === "blocked_invalid") {
      const field = drafts.getFirstInvalidField();
      if (field) focusInvalid(field);
      return;
    }
    setOpenSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const runConfirm = (
    action:
      | { kind: "confirm_geometry" }
      | { kind: "confirm_construction" }
      | { kind: "confirm_technical" }
      | { kind: "confirm_relation"; relationId: string },
  ) => {
    const snap = drafts.takePendingUpdates();
    if (snap.status === "blocked_invalid") {
      const field = drafts.getFirstInvalidField();
      if (field) focusInvalid(field);
      return;
    }
    const updates = snap.updates;
    const patch = buildAcmPanelConfirmActionWithUpdatesPatch({
      finishSetup,
      updates,
      action:
        action.kind === "confirm_relation"
          ? { kind: "confirm_relation", relationId: action.relationId, status: "confirmed" }
          : action,
    });
    if (!patch) return;
    actions.onApplyFinishPatch(patch);
    if (updates.length) {
      drafts.markClean(updates.map((u) => u.field as AcmPanelDraftNumericField));
    }
  };

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
        onToggle={() => requestSectionToggle("summary")}
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
          <p>
            Segmente: {model.segmentCount} ({model.segmentedLabel})
          </p>
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
        onToggle={() => requestSectionToggle("geometry")}
        status={authorityHintForField(model, "panel_geometry").label}
      >
        <div className="grid gap-2 sm:grid-cols-2">
          <DraftNumberInput
            field="panel_width_mm"
            label="Lățime (mm)"
            drafts={drafts}
            model={model}
            authorityKey="panel_geometry"
          />
          <DraftNumberInput
            field="panel_height_mm"
            label="Înălțime (mm)"
            drafts={drafts}
            model={model}
            authorityKey="panel_geometry"
          />
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
          data-testid="intake-v6-acm-confirm-geometry"
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => runConfirm({ kind: "confirm_geometry" })}
        >
          Confirmă geometria
        </button>
      </Section>

      <Section
        id="construction"
        title="Construcție"
        open={openSections.construction}
        onToggle={() => requestSectionToggle("construction")}
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
          <DraftNumberInput
            field="acm_thickness_mm"
            label="Grosime ACM"
            drafts={drafts}
            model={model}
            authorityKey="acm_thickness_mm"
          />
          <DraftNumberInput
            field="l1_mm"
            label="Perete / întoarcere"
            drafts={drafts}
            model={model}
            authorityKey="l1_mm"
          />
          <DraftNumberInput
            field="l2_mm"
            label="Buză interioară"
            drafts={drafts}
            model={model}
            authorityKey="l2_mm"
          />
          <DraftNumberInput
            field="fold_count"
            label="Fold count"
            drafts={drafts}
            model={model}
            authorityKey="fold_count"
          />
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded border border-amber-500/35 px-2 py-1 text-[11px] text-amber-100"
            data-testid="intake-v6-acm-confirm-construction"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => runConfirm({ kind: "confirm_construction" })}
          >
            Confirmă valorile din construcție
          </button>
          <button
            type="button"
            className="rounded border border-emerald-500/35 px-2 py-1 text-[11px] text-emerald-100"
            data-testid="intake-v6-acm-confirm-technical"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => runConfirm({ kind: "confirm_technical" })}
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
        onToggle={() => requestSectionToggle("segments")}
        status={model.segmentedLabel}
      >
        <IntakeV6SegmentedBackgroundPanel
          finish={finishSetup}
          onPatch={(patch) => {
            const flush = drafts.flushAll();
            if (flush.status === "blocked_invalid") {
              const field = drafts.getFirstInvalidField();
              if (field) focusInvalid(field);
              return;
            }
            actions.onSegmentedPatch(patch);
          }}
        />
      </Section>

      <Section
        id="material"
        title="Material și finisaj"
        open={openSections.material}
        onToggle={() => requestSectionToggle("material")}
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
        onToggle={() => requestSectionToggle("structure")}
      >
        <p className="text-[11px] text-slate-300">
          Cadru interior: {cfg.internal_frame_enabled ? "activ" : "inactiv"}
        </p>
        <p className="mt-1 text-[10px] text-slate-500">
          Montajul pe perete / structură se confirmă explicit ca relație operațională — nu din
          geometrie.
        </p>
        {model.mountingRelations.length === 0 ? (
          <p className="mt-1 text-[11px] text-slate-500">
            Nicio relație mounts_on / attached_to_structure.
          </p>
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
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() =>
                      runConfirm({ kind: "confirm_relation", relationId: rel.relation_id })
                    }
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
        onToggle={() => requestSectionToggle("relations")}
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
        onToggle={() => requestSectionToggle("technical")}
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
});

export default IntakeV6AcmPanelInspector;
