/**
 * Operator confirmation for multi-panel ACM/ACP backgrounds.
 * Proposal from analyzer; confirm/reject writes finish_setup.segmented_background.
 */
import {
  buildConfirmSegmentedBackgroundPatch,
  buildRejectSegmentedBackgroundPatch,
  confirmationBlocked,
  readSegmentedBackground,
  SEGMENTED_MESSAGES_RO,
  statusLabelRo,
  type SegmentedBackground,
} from "@/lib/intakeV6/segmentedBackground";

function constructionLabel(code: string): string {
  switch (code) {
    case "APPLIED_VOLUMETRIC_LETTER":
      return "Litera volumetrica aplicata";
    case "SIMPLE_APPLIED":
      return "Element aplicat";
    case "CUTOUT":
      return "Decupaj";
    case "ACRYLIC_INSERT":
      return "Insert plexiglas 10 mm";
    default:
      return code;
  }
}

export default function IntakeV6SegmentedBackgroundPanel({
  finish,
  disabled,
  onPatch,
}: {
  finish: Record<string, unknown> | null | undefined;
  disabled?: boolean;
  onPatch: (patch: { segmented_background: SegmentedBackground }) => void;
}) {
  const config = readSegmentedBackground(finish);
  if (!config) return null;

  const status = String(config.status || "").toUpperCase();
  if (status === "SINGLE_PANEL") return null;
  if (status === "INACTIVE" && !config.panels?.length) return null;

  const blockers = confirmationBlocked(config);
  const canConfirm = status === "PROPOSED" && blockers.length === 0;
  const bindings = config.element_bindings || [];
  const hasDistributed =
    new Set(bindings.filter((b) => !b.crosses_joint).map((b) => b.primary_panel_id)).size >= 2;
  const appliedCrossings = bindings.filter(
    (b) => b.crosses_joint && (b.construction_type === "APPLIED_VOLUMETRIC_LETTER" || b.construction_type === "SIMPLE_APPLIED"),
  );
  const cutoutCrossings = bindings.filter((b) => b.crosses_joint && b.construction_type === "CUTOUT");
  const insertCrossings = bindings.filter(
    (b) => b.crosses_joint && b.construction_type === "ACRYLIC_INSERT",
  );

  return (
    <div
      className="mt-3 rounded border border-amber-500/35 bg-amber-950/15 px-3 py-3 space-y-3"
      data-testid="intake-v6-segmented-background-panel"
      data-status={status.toLowerCase()}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[11px] font-semibold text-amber-100">
            Posibil fundal format din mai multe panouri
          </p>
          <p className="text-[10px] text-slate-400 mt-0.5">
            {status === "CONFIRMED"
              ? SEGMENTED_MESSAGES_RO.confirmed
              : status === "REJECTED"
                ? SEGMENTED_MESSAGES_RO.rejected
                : SEGMENTED_MESSAGES_RO.proposal}
          </p>
        </div>
        <span
          className="shrink-0 rounded border border-amber-500/40 px-1.5 py-0.5 text-[10px] text-amber-100"
          data-testid="intake-v6-segmented-status"
        >
          {statusLabelRo(status)}
        </span>
      </div>

      <div data-testid="intake-v6-segmented-panel-list" className="space-y-1.5">
        <p className="text-[10px] font-medium text-slate-300">Panouri</p>
        <ul className="space-y-1">
          {(config.panels || []).map((panel) => (
            <li
              key={panel.panel_id}
              className="rounded border border-[#2A3548] bg-[#0A0F1A]/80 px-2 py-1.5 text-[10px] text-slate-200"
              data-testid={`intake-v6-segmented-panel-${panel.panel_id}`}
            >
              <span className="font-medium text-amber-50">{panel.panel_id}</span>
              {" · "}ordine {panel.order}
              {" · "}
              {panel.width_mm ?? "—"} × {panel.height_mm ?? "—"} mm
              {" · "}x={panel.position?.x_mm ?? 0}
            </li>
          ))}
        </ul>
      </div>

      {(config.joints || []).length > 0 ? (
        <div data-testid="intake-v6-segmented-joints">
          <p className="text-[10px] font-medium text-slate-300">Imbinari</p>
          <ul className="mt-1 space-y-0.5 text-[10px] text-slate-400">
            {config.joints.map((j) => (
              <li key={j.joint_id}>
                {j.left_panel_id} ↔ {j.right_panel_id} ({j.orientation === "VERTICAL" ? "verticala" : j.orientation})
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div data-testid="intake-v6-segmented-element-summary" className="space-y-1 text-[10px]">
        <p className="font-medium text-slate-300">Elemente</p>
        {hasDistributed ? (
          <p className="text-slate-300" data-testid="intake-v6-segmented-distributed">
            {SEGMENTED_MESSAGES_RO.distributed}
          </p>
        ) : null}
        {appliedCrossings.map((b) => (
          <p key={b.binding_id} className="text-cyan-200" data-testid="intake-v6-segmented-applied-crossing">
            {constructionLabel(b.construction_type)} ({b.element_ref || b.binding_id}):{" "}
            {SEGMENTED_MESSAGES_RO.appliedCrossing}
          </p>
        ))}
        {cutoutCrossings.map((b) => (
          <p key={b.binding_id} className="text-rose-300" data-testid="intake-v6-segmented-cutout-blocker">
            {SEGMENTED_MESSAGES_RO.cutoutBlocker}
          </p>
        ))}
        {insertCrossings.map((b) => (
          <p key={b.binding_id} className="text-rose-300" data-testid="intake-v6-segmented-insert-blocker">
            {SEGMENTED_MESSAGES_RO.insertBlocker}
          </p>
        ))}
        {!hasDistributed && !appliedCrossings.length && !cutoutCrossings.length && !insertCrossings.length ? (
          <p className="text-slate-500">Nicio legatura element–panou in propunere.</p>
        ) : null}
      </div>

      {blockers.length > 0 && status === "PROPOSED" ? (
        <ul
          className="rounded border border-rose-500/40 bg-rose-950/20 px-2 py-1.5 space-y-0.5"
          data-testid="intake-v6-segmented-confirm-blockers"
        >
          {blockers.map((msg) => (
            <li key={msg} className="text-[10px] text-rose-200">
              {msg}
            </li>
          ))}
        </ul>
      ) : null}

      {status === "PROPOSED" ? (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={disabled || !canConfirm}
            className="rounded border border-emerald-500/50 bg-emerald-950/40 px-2.5 py-1 text-[11px] text-emerald-100 disabled:opacity-40"
            data-testid="intake-v6-segmented-confirm"
            onClick={() => onPatch(buildConfirmSegmentedBackgroundPatch(config))}
          >
            Confirma
          </button>
          <button
            type="button"
            disabled={disabled}
            className="rounded border border-slate-500/50 bg-slate-900/50 px-2.5 py-1 text-[11px] text-slate-200 disabled:opacity-40"
            data-testid="intake-v6-segmented-reject"
            onClick={() => onPatch(buildRejectSegmentedBackgroundPatch(config))}
          >
            Respinge
          </button>
        </div>
      ) : null}

      {status === "CONFIRMED" ? (
        <p className="text-[10px] text-emerald-200" data-testid="intake-v6-segmented-confirmed-banner">
          {SEGMENTED_MESSAGES_RO.confirmed}
        </p>
      ) : null}

      <p className="text-[9px] text-slate-500">
        Analizatorul doar propune. Confirmarea este a operatorului. Fara pret, fara Execution, fara taskuri.
      </p>
    </div>
  );
}
