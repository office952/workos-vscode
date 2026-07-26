/**
 * Operator UI for per-panel 220V service points on confirmed segmented assemblies.
 */
import {
  buildConfirmElectricalPatch,
  buildDraftElectricalPatch,
  electricalConfirmBlocked,
  ELECTRICAL_MESSAGES_RO,
  ensureElectricalForPanels,
  POSITION_LABELS_RO,
  readSegmentedElectrical,
  SUPPLY_LABELS_RO,
  type ElectricalSupplyMode,
  type PanelElectrical,
  type SegmentedElectrical,
  type ServicePointPosition,
} from "@/lib/intakeV6/segmentedElectrical";
import { readSegmentedBackground } from "@/lib/intakeV6/segmentedBackground";
import { electricalAssemblyStatusLabelRo } from "@/lib/intakeV6/intakeV6OperatorVocabulary";

const SUPPLY_OPTIONS: ElectricalSupplyMode[] = [
  "UNCONFIRMED",
  "DIRECT_220V",
  "SHARED_FROM_PANEL",
  "NO_LOCAL_220V",
];

const POSITION_OPTIONS: ServicePointPosition[] = [
  "TOP_LEFT",
  "TOP_RIGHT",
  "BOTTOM_LEFT",
  "BOTTOM_RIGHT",
  "TOP_CENTER",
  "BOTTOM_CENTER",
  "LEFT_CENTER",
  "RIGHT_CENTER",
  "CUSTOM",
  "NONE",
];

function updatePanel(
  electrical: SegmentedElectrical,
  panelId: string,
  patch: Partial<PanelElectrical>,
): SegmentedElectrical {
  return {
    ...electrical,
    status: electrical.status === "CONFIRMED" ? "DRAFT" : electrical.status,
    operator_confirmed: false,
    panels: electrical.panels.map((p) => (p.panel_id === panelId ? { ...p, ...patch } : p)),
  };
}

export default function IntakeV6SegmentedElectricalPanel({
  finish,
  disabled,
  onPatchSegmented,
}: {
  finish: Record<string, unknown> | null | undefined;
  disabled?: boolean;
  onPatchSegmented: (segmented: Record<string, unknown>) => void;
}) {
  const segmented = readSegmentedBackground(finish);
  if (!segmented || String(segmented.status).toUpperCase() !== "CONFIRMED") return null;
  if ((segmented.panels || []).length < 2) return null;

  const panelIds = (segmented.panels || []).map((p) => p.panel_id);
  const electrical = ensureElectricalForPanels(panelIds, readSegmentedElectrical(segmented as unknown as Record<string, unknown>));
  const status = String(electrical.status || "DRAFT").toUpperCase();
  const blockers = electricalConfirmBlocked(electrical);
  const canConfirm = status !== "CONFIRMED" && blockers.length === 0;

  const persist = (next: SegmentedElectrical) => {
    onPatchSegmented({
      ...(segmented as unknown as Record<string, unknown>),
      electrical_connection_management: next,
    });
  };

  return (
    <div
      className="mt-3 rounded border border-sky-500/35 bg-sky-950/15 px-3 py-3 space-y-3"
      data-testid="intake-v6-segmented-electrical-panel"
      data-status={status.toLowerCase()}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[11px] font-semibold text-sky-100">Alimentare 220V pe panouri</p>
          <p className="text-[10px] text-slate-400 mt-0.5">
            {status === "CONFIRMED"
              ? ELECTRICAL_MESSAGES_RO.confirmed
              : ELECTRICAL_MESSAGES_RO.indicate}
          </p>
        </div>
        <span
          className="shrink-0 rounded border border-sky-500/40 px-1.5 py-0.5 text-[10px] text-sky-100"
          data-testid="intake-v6-segmented-electrical-status"
        >
          {electricalAssemblyStatusLabelRo(status)}
        </span>
      </div>

      <div className="space-y-3" data-testid="intake-v6-segmented-electrical-panels">
        {electrical.panels.map((panel) => {
          const otherPanels = panelIds.filter((id) => id !== panel.panel_id);
          return (
            <div
              key={panel.panel_id}
              className="rounded border border-wo-border-strong bg-wo-surface-inset/80 px-2.5 py-2 space-y-2"
              data-testid={`intake-v6-segmented-electrical-${panel.panel_id}`}
            >
              <p className="text-[10px] font-medium text-sky-50">
                {panel.panel_id}
                <span className="text-slate-500"> · panou fizic</span>
              </p>

              <label className="block text-[10px] text-slate-400">
                Sursa 220V
                <select
                  className="mt-0.5 w-full rounded border border-wo-border-strong bg-wo-surface-input px-2 py-1 text-[11px] text-wo-text-primary"
                  disabled={disabled || status === "CONFIRMED"}
                  value={panel.supply_mode}
                  data-testid={`intake-v6-elec-supply-${panel.panel_id}`}
                  onChange={(e) => {
                    const mode = e.target.value as ElectricalSupplyMode;
                    persist(
                      updatePanel(electrical, panel.panel_id, {
                        supply_mode: mode,
                        shared_from_panel_id: mode === "SHARED_FROM_PANEL" ? otherPanels[0] || null : null,
                        service_point_position:
                          mode === "DIRECT_220V"
                            ? panel.service_point_position || "TOP_RIGHT"
                            : mode === "UNCONFIRMED"
                              ? null
                              : "NONE",
                      }),
                    );
                  }}
                >
                  {SUPPLY_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {SUPPLY_LABELS_RO[opt]}
                    </option>
                  ))}
                </select>
              </label>

              {panel.supply_mode === "DIRECT_220V" ? (
                <label className="block text-[10px] text-slate-400">
                  Pozitie alimentare
                  <select
                    className="mt-0.5 w-full rounded border border-wo-border-strong bg-wo-surface-input px-2 py-1 text-[11px] text-wo-text-primary"
                    disabled={disabled || status === "CONFIRMED"}
                    value={panel.service_point_position || ""}
                    data-testid={`intake-v6-elec-position-${panel.panel_id}`}
                    onChange={(e) =>
                      persist(
                        updatePanel(electrical, panel.panel_id, {
                          service_point_position: (e.target.value || null) as ServicePointPosition | null,
                        }),
                      )
                    }
                  >
                    <option value="">— selecteaza —</option>
                    {POSITION_OPTIONS.filter((p) => p !== "NONE").map((opt) => (
                      <option key={opt} value={opt}>
                        {POSITION_LABELS_RO[opt]}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              {panel.supply_mode === "SHARED_FROM_PANEL" ? (
                <label className="block text-[10px] text-slate-400">
                  Primeste din panoul
                  <select
                    className="mt-0.5 w-full rounded border border-wo-border-strong bg-wo-surface-input px-2 py-1 text-[11px] text-wo-text-primary"
                    disabled={disabled || status === "CONFIRMED"}
                    value={panel.shared_from_panel_id || ""}
                    data-testid={`intake-v6-elec-shared-${panel.panel_id}`}
                    onChange={(e) =>
                      persist(
                        updatePanel(electrical, panel.panel_id, {
                          shared_from_panel_id: e.target.value || null,
                        }),
                      )
                    }
                  >
                    <option value="">— selecteaza —</option>
                    {otherPanels.map((id) => (
                      <option key={id} value={id}>
                        {id}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              {panel.service_point_position === "CUSTOM" ? (
                <label className="block text-[10px] text-slate-400">
                  Nota / schita
                  <input
                    className="mt-0.5 w-full rounded border border-wo-border-strong bg-wo-surface-input px-2 py-1 text-[11px] text-wo-text-primary"
                    disabled={disabled || status === "CONFIRMED"}
                    value={panel.custom_position_note || panel.sketch_ref || ""}
                    data-testid={`intake-v6-elec-custom-${panel.panel_id}`}
                    onChange={(e) =>
                      persist(
                        updatePanel(electrical, panel.panel_id, {
                          custom_position_note: e.target.value,
                          sketch_ref: e.target.value,
                        }),
                      )
                    }
                  />
                </label>
              ) : null}

              <label className="block text-[10px] text-slate-400">
                Iesire cablu / directie atelier
                <input
                  className="mt-0.5 w-full rounded border border-wo-border-strong bg-wo-surface-input px-2 py-1 text-[11px] text-wo-text-primary"
                  disabled={disabled || status === "CONFIRMED"}
                  placeholder="ex: spre coltul dreapta sus"
                  value={panel.routing_direction_note_ro || ""}
                  data-testid={`intake-v6-elec-routing-${panel.panel_id}`}
                  onChange={(e) =>
                    persist(
                      updatePanel(electrical, panel.panel_id, {
                        routing_direction_note_ro: e.target.value,
                        workshop_prep: {
                          ...(panel.workshop_prep || {}),
                          cables_routed_toward_service: Boolean(e.target.value),
                        },
                      }),
                    )
                  }
                />
              </label>

              <div className="flex flex-wrap gap-3 text-[10px] text-slate-300">
                <label className="inline-flex items-center gap-1">
                  <input
                    type="checkbox"
                    disabled={disabled || status === "CONFIRMED"}
                    checked={Boolean(panel.workshop_prep?.reserve_required)}
                    onChange={(e) =>
                      persist(
                        updatePanel(electrical, panel.panel_id, {
                          workshop_prep: {
                            ...(panel.workshop_prep || {}),
                            reserve_required: e.target.checked,
                          },
                        }),
                      )
                    }
                  />
                  Rezerva cablu
                </label>
                <label className="inline-flex items-center gap-1">
                  <input
                    type="checkbox"
                    disabled={disabled || status === "CONFIRMED"}
                    checked={Boolean(panel.installation?.finalize_after_alignment)}
                    onChange={(e) =>
                      persist(
                        updatePanel(electrical, panel.panel_id, {
                          installation: {
                            ...(panel.installation || {}),
                            finalize_after_alignment: e.target.checked,
                            connect_to_client_220v: panel.supply_mode === "DIRECT_220V",
                          },
                        }),
                      )
                    }
                  />
                  Finalizare dupa aliniere
                </label>
              </div>

              {panel.supply_mode === "UNCONFIRMED" ? (
                <p className="text-[10px] text-amber-200/90" data-testid={`intake-v6-elec-unresolved-${panel.panel_id}`}>
                  {ELECTRICAL_MESSAGES_RO.unconfirmed}
                </p>
              ) : null}
              {panel.supply_mode === "SHARED_FROM_PANEL" && panel.shared_from_panel_id ? (
                <p className="text-[10px] text-cyan-200/90">
                  Panoul {panel.panel_id} primeste alimentarea din {panel.shared_from_panel_id}.
                </p>
              ) : null}
            </div>
          );
        })}
      </div>

      {(electrical.inter_panel_connections || []).length > 0 ? (
        <div data-testid="intake-v6-segmented-electrical-links" className="text-[10px] text-slate-300 space-y-1">
          <p className="font-medium text-slate-200">Legaturi inter-panou</p>
          {electrical.inter_panel_connections.map((c) => (
            <p key={c.connection_id}>
              {c.source_panel_id} → {c.destination_panel_id}
              {c.alignment_dependent ? ` · ${ELECTRICAL_MESSAGES_RO.afterAlignment}` : ""}
              {c.reserve_required ? ` · ${ELECTRICAL_MESSAGES_RO.reserve}` : ""}
            </p>
          ))}
        </div>
      ) : null}

      {blockers.length > 0 && status !== "CONFIRMED" ? (
        <ul className="rounded border border-amber-500/40 bg-amber-950/20 px-2 py-1.5 space-y-0.5" data-testid="intake-v6-elec-blockers">
          {blockers.map((msg) => (
            <li key={msg} className="text-[10px] text-amber-100">
              {msg}
            </li>
          ))}
        </ul>
      ) : null}

      {status !== "CONFIRMED" ? (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={disabled || !canConfirm}
            className="rounded border border-emerald-500/50 bg-emerald-950/40 px-2.5 py-1 text-[11px] text-emerald-100 disabled:opacity-40"
            data-testid="intake-v6-segmented-electrical-confirm"
            onClick={() => {
              const withLinks = maybeAutoSharedLinks(electrical);
              persist(buildConfirmElectricalPatch(withLinks));
            }}
          >
            Confirma configuratia electrica
          </button>
        </div>
      ) : (
        <button
          type="button"
          disabled={disabled}
          className="rounded border border-slate-500/50 bg-slate-900/50 px-2.5 py-1 text-[11px] text-slate-200"
          data-testid="intake-v6-segmented-electrical-edit"
          onClick={() => persist(buildDraftElectricalPatch(electrical))}
        >
          Editeaza configuratia electrica
        </button>
      )}

      <p className="text-[9px] text-slate-500">
        Context de ansamblu (shell). LED/cablaj local raman pe litere. Fara pret, fara dimensionare PSU, fara taskuri Execution.
      </p>
    </div>
  );
}

function maybeAutoSharedLinks(electrical: SegmentedElectrical): SegmentedElectrical {
  const links = [...(electrical.inter_panel_connections || [])];
  for (const panel of electrical.panels) {
    if (panel.supply_mode !== "SHARED_FROM_PANEL" || !panel.shared_from_panel_id) continue;
    const id = `ec_${panel.shared_from_panel_id}_${panel.panel_id}`;
    if (links.some((l) => l.connection_id === id)) continue;
    links.push({
      connection_id: id,
      source_panel_id: panel.shared_from_panel_id,
      destination_panel_id: panel.panel_id,
      connection_type: "LV_FEED",
      alignment_dependent: true,
      prepared_in_workshop: true,
      completed_on_site: true,
      reserve_required: true,
      length_is_estimate: true,
      notes_ro: ELECTRICAL_MESSAGES_RO.afterAlignment,
    });
  }
  return { ...electrical, inter_panel_connections: links };
}
