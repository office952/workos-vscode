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
import { intakeV6ShowOperatorConfigStatusBadges } from "@/lib/intakeV6/intakeV6OperatorConfigStatusChrome";
import AcmPanelProductionGeometryBlock from "./AcmPanelProductionGeometryBlock";
import IntakeV6AcmShellFinishPanel from "./IntakeV6AcmShellFinishPanel";
import { readAcmShellFinishFromInstance } from "@/lib/intakeV6/acmPanel/shellFinish";

export type AcmPanelInspectorActions = {
  onApplyFinishPatch: (patch: Partial<IntakeV6FinishSetup>) => void;
  onSegmentedPatch: (patch: { segmented_background: SegmentedBackground }) => void;
  onProductionGeometryBound?: () => void;
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
  flat = false,
}: {
  id: string;
  title: string;
  open: boolean;
  onToggle: () => void;
  status?: string;
  children: ReactNode;
  /** Flat workbench: always-open block, no accordion chrome */
  flat?: boolean;
}) {
  if (flat) {
    return (
      <div
        className="space-y-2 border-b border-wo-border-strong/50 pb-3 last:border-b-0 last:pb-0"
        data-testid={`intake-v6-acm-section-${id}`}
        data-open="true"
        data-presentation="flat"
      >
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-[12px] font-semibold text-slate-100">{title}</h3>
          {status ? (
            <span className="rounded border border-amber-500/25 px-1.5 py-0.5 text-[10px] text-amber-200">
              {status}
            </span>
          ) : null}
        </div>
        <div>{children}</div>
      </div>
    );
  }

  return (
    <div
      className="rounded border border-wo-border-strong/60 bg-wo-surface-inset/35"
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
      {open ? <div className="border-t border-wo-border-strong/50 px-2.5 py-2">{children}</div> : null}
    </div>
  );
}

function AuthorityHint({ model, fieldKey }: { model: AcmPanelUiReadModel; fieldKey: string }) {
  if (!intakeV6ShowOperatorConfigStatusBadges()) return null;
  const hint = authorityHintForField(model, fieldKey);
  return (
    <span className="text-[10px] text-slate-500" data-testid={`intake-v6-acm-authority-${fieldKey}`}>
      {hint.label}
    </span>
  );
}

function sectionStatus(label: string | undefined): string | undefined {
  if (!intakeV6ShowOperatorConfigStatusBadges()) return undefined;
  return label;
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
        className={`mt-0.5 w-full rounded border bg-wo-surface-inset px-2 py-1.5 text-[11px] ${
          props.status === "invalid"
            ? "border-rose-500/50 text-rose-100"
            : "border-wo-border-strong text-slate-100"
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
    workspaceId?: string | null;
    /** flat = workbench Panou/carcasă (primary sections always open) */
    presentation?: "accordion" | "flat";
  }
>(function IntakeV6AcmPanelInspector(
  {
    model,
    finishSetup,
    actions,
    focusIssue,
    onFocusConsumed,
    workspaceId,
    presentation = "accordion",
  },
  ref,
) {
  const flat = presentation === "flat";
  const constructionNeedsAttention =
    model.issues.some((issue) => issue.sectionId === "construction") ||
    Object.values(model.fieldAuthority ?? {}).some(
      (value) => value === "catalog_default" || value === "proposed",
    );
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    summary: true,
    geometry: true,
    construction: flat || constructionNeedsAttention,
    segments: false,
    material: flat,
    structure: false,
    relations: false,
    technical: false,
  });

  useEffect(() => {
    if (!constructionNeedsAttention) return;
    setOpenSections((prev) => (prev.construction ? prev : { ...prev, construction: true }));
  }, [constructionNeedsAttention]);
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
      | { kind: "confirm_panel" }
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
        className="rounded border border-wo-border-strong/50 px-3 py-4 text-[12px] text-slate-400"
        data-testid="intake-v6-acm-panel-inspector"
      >
        Niciun Alucobond casetat instanțiat pe acest workspace.
      </section>
    );
  }

  const inst = model.instance;
  const cfg = inst.configuration;
  const shellConfirmed = readAcmShellFinishFromInstance(inst).operator_confirmed;
  const panelConfirmed =
    inst.technical_configuration_status === "confirmed" && shellConfirmed;

  return (
    <section
      ref={rootRef}
      className={flat ? "space-y-3 rounded-lg border border-wo-border-strong/70 bg-wo-surface-input/40 p-3" : "space-y-2"}
      data-testid="intake-v6-acm-panel-inspector"
      data-presentation={flat ? "flat" : "accordion"}
    >
      <Section
        id="summary"
        title="Rezumat"
        open={openSections.summary}
        onToggle={() => requestSectionToggle("summary")}
        status={sectionStatus(model.primaryStatus.label)}
        flat={flat}
      >
        <div className="space-y-1 text-[11px] text-slate-300" data-testid="intake-v6-acm-summary">
          <p className="text-[13px] font-semibold text-slate-100">{model.label}</p>
          <p>Dimensiuni: {model.dimensionsSummary ?? "—"}</p>
          {intakeV6ShowOperatorConfigStatusBadges() ? (
            flat ? (
              <p className="text-slate-500" data-testid="intake-v6-acm-summary-association">
                {model.association.label} · {model.technical.label}
              </p>
            ) : (
              <>
                <p data-testid="intake-v6-acm-summary-association">
                  Asociere: {model.association.label}
                </p>
                <p>Tehnic: {model.technical.label}</p>
                <p>Compoziție: {model.composition.label}</p>
                <p>
                  Segmente: {model.segmentCount} ({model.segmentedLabel})
                </p>
              </>
            )
          ) : (
            <p data-testid="intake-v6-acm-summary-association">
              Segmente: {model.segmentCount}
            </p>
          )}
          {intakeV6ShowOperatorConfigStatusBadges() && model.unresolvedConfirmations.length ? (
            <p className="text-amber-200">
              Nerezolvat: {model.unresolvedConfirmations.join(" · ")}
            </p>
          ) : null}
        </div>
      </Section>

      <Section
        id="geometry"
        title="Geometrie"
        open={openSections.geometry}
        onToggle={() => requestSectionToggle("geometry")}
        status={sectionStatus(authorityHintForField(model, "panel_geometry").label)}
        flat={flat}
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
        <AcmPanelProductionGeometryBlock
          workspaceId={workspaceId}
          componentInstanceId={inst.component_instance_id}
          instance={inst as unknown as Record<string, unknown>}
          onBound={() => actions.onProductionGeometryBound?.()}
        />
      </Section>

      <Section
        id="construction"
        title="Construcție panou"
        open={openSections.construction}
        onToggle={() => requestSectionToggle("construction")}
        status={sectionStatus(model.technical.label)}
        flat={flat}
      >
        <div
          className="grid gap-2 sm:grid-cols-2"
          data-testid="intake-v6-acm-casing-fields"
        >
          <label className="block text-[11px]">
            <span className="text-slate-500">Pliuri</span>
            <select
              className="mt-0.5 w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[11px] text-slate-100"
              data-testid="intake-v6-acm-field-fold_count"
              value={String(drafts.getFieldProps("fold_count").value || cfg.fold_count || 1)}
              onChange={(e) => drafts.getFieldProps("fold_count").onChange(e.target.value)}
              onBlur={() => drafts.getFieldProps("fold_count").onBlur()}
            >
              <option value="1">1 pliu</option>
              <option value="2">2 pliuri</option>
            </select>
            <AuthorityHint model={model} fieldKey="fold_count" />
          </label>
          <DraftNumberInput
            field="acm_thickness_mm"
            label="Grosime (mm)"
            drafts={drafts}
            model={model}
            authorityKey="acm_thickness_mm"
          />
          <DraftNumberInput
            field="l1_mm"
            label="Pliu 1 (mm)"
            drafts={drafts}
            model={model}
            authorityKey="l1_mm"
          />
          {Number(drafts.getFieldProps("fold_count").value || cfg.fold_count) === 2 ? (
            <DraftNumberInput
              field="l2_mm"
              label="Pliu 2 (mm)"
              drafts={drafts}
              model={model}
              authorityKey="l2_mm"
            />
          ) : (
            <label className="block text-[11px]">
              <span className="text-slate-500">Adâncime (mm)</span>
              <input
                type="text"
                readOnly
                className="mt-0.5 w-full rounded border border-wo-border-strong/70 bg-wo-surface-inset/60 px-2 py-1.5 text-[11px] text-slate-400"
                value={String(drafts.getFieldProps("l1_mm").value || cfg.l1_mm || "")}
                title="finished_depth_mm = L1"
                data-testid="intake-v6-acm-field-finished_depth_mm"
              />
            </label>
          )}
        </div>
        <p className="mt-2 text-[10px] text-slate-500">
          Valorile se salvează pe măsură ce editezi. Confirmarea e o singură dată, la final.
        </p>
      </Section>

      <Section
        id="segments"
        title="Segmente"
        open={openSections.segments}
        onToggle={() => requestSectionToggle("segments")}
        status={sectionStatus(model.segmentedLabel)}
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
        flat={flat}
      >
        <IntakeV6AcmShellFinishPanel
          finishSetup={finishSetup}
          onApplyFinishPatch={actions.onApplyFinishPatch}
          hideConfirmButton
        />
      </Section>

      <Section
        id="structure"
        title="Structură și montaj"
        open={openSections.structure}
        onToggle={() => requestSectionToggle("structure")}
      >
        <label
          className="flex items-start gap-2 text-[11px] text-slate-300"
          data-testid="intake-v6-acm-field-internal_frame_enabled"
        >
          <input
            type="checkbox"
            className="mt-0.5"
            checked={Boolean(cfg.internal_frame_enabled)}
            onChange={(e) => {
              const flush = drafts.flushAll();
              if (flush.status === "blocked_invalid") {
                const field = drafts.getFirstInvalidField();
                if (field) focusInvalid(field);
                return;
              }
              const patch = buildAcmPanelUpdateFieldsPatch({
                finishSetup,
                updates: [
                  {
                    field: "internal_frame_enabled",
                    value: e.target.checked,
                    confirmAuthority: true,
                  },
                ],
              });
              if (patch) actions.onApplyFinishPatch(patch);
            }}
          />
          <span className="font-medium text-slate-200">Cadru interior</span>
        </label>
        {model.mountingRelations.length === 0 ? (
          <p className="mt-2 text-[11px] text-slate-500">Nicio relație de montaj confirmată.</p>
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

      <div
        className="sticky bottom-0 z-10 border-t border-wo-border-strong/70 bg-wo-surface-input/95 px-1 py-2 backdrop-blur-sm"
        data-testid="intake-v6-acm-final-confirm-bar"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          {intakeV6ShowOperatorConfigStatusBadges() ? (
            <p className="text-[11px] text-slate-400">
              {panelConfirmed ? (
                <span className="text-emerald-300">Panou confirmat</span>
              ) : (
                <span className="text-amber-200/90">
                  O singură confirmare: geometrie, construcție și finisaj
                </span>
              )}
            </p>
          ) : (
            <p className="text-[11px] text-slate-400">
              Geometrie, construcție și finisaj — o singură acțiune
            </p>
          )}
          <button
            type="button"
            className="rounded-md border border-emerald-400/50 bg-emerald-500/20 px-3 py-1.5 text-[12px] font-semibold text-emerald-50 hover:bg-emerald-500/30"
            data-testid="intake-v6-acm-confirm-panel"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => runConfirm({ kind: "confirm_panel" })}
          >
            Confirmă panoul Alucobond
          </button>
        </div>
      </div>
    </section>
  );
});

export default IntakeV6AcmPanelInspector;
