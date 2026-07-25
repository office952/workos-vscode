/**
 * ACM shell foil — operator-simple capture on acm_panel_instance.shell_finish.
 * Primary: how foil is applied + față/cant checkboxes. Workshop fields stay collapsed.
 */
import { useEffect, useMemo, useState } from "react";
import type { IntakeV6FinishSetup } from "@/lib/intakeV6/intakeV6Api";
import { resolveAcmPanelInstance } from "@/lib/intakeV6/acmPanel/resolveInstance";
import { buildAcmPanelShellFinishPatch } from "@/lib/intakeV6/acmPanel/operatorPatch";
import {
  ACM_SHELL_FOIL_STRATEGY_OPTIONS,
  ACM_SHELL_ZONE_KIND_OPTIONS,
  defaultAcmShellZone,
  normalizeAcmShellFinish,
  readAcmShellFinishFromInstance,
  shellNeedsFoil,
  summarizeAcmShellFinishOperatorRo,
  zoneNeedsFoil,
  type AcmShellFinishContract,
  type AcmShellFoilStrategyMode,
  type AcmShellZoneFinish,
  type AcmShellZoneKind,
} from "@/lib/intakeV6/acmPanel/shellFinish";
import {
  INTAKE_V4_ORACAL_FACE_ROLL_WIDTH_OPTIONS,
  PRINT_LAMINATION_ROLL_WIDTH_OPTIONS,
} from "@/lib/intakeV6/intakeV4FaceFinishOptions";
import { intakeV6ShowOperatorConfigStatusBadges } from "@/lib/intakeV6/intakeV6OperatorConfigStatusChrome";
type Props = {
  finishSetup: IntakeV6FinishSetup | Record<string, unknown> | null | undefined;
  onApplyFinishPatch: (patch: Partial<IntakeV6FinishSetup>) => void;
  /** When true, confirm is owned by the parent ACM panel final button. */
  hideConfirmButton?: boolean;
};
type FoilApplyMode = "after_frame" | "none";
function preserveOrDefaultFoilZone(zone: AcmShellZoneFinish): AcmShellZoneFinish {
  return zoneNeedsFoil(zone) ? zone : defaultAcmShellZone("oracal_651");
}
function AtelierZoneFields({
  zoneId,
  labelRo,
  zone,
  onChange,
}: {
  zoneId: "face" | "volume";
  labelRo: string;
  zone: AcmShellZoneFinish;
  onChange: (next: AcmShellZoneFinish) => void;
}) {
  return (
    <div className="space-y-1.5 rounded border border-[#2A3548]/60 bg-[#0A0F1A]/40 px-2 py-2">
      <p className="text-[11px] font-semibold text-slate-300">{labelRo}</p>
      <select
        className="w-full rounded border border-[#2A3548] bg-[#111827] px-2 py-1.5 text-[12px] text-slate-100"
        value={zone.kind}
        onChange={(e) => onChange(defaultAcmShellZone(e.target.value as AcmShellZoneKind))}
        data-testid={`intake-v6-acm-shell-zone-kind-${zoneId}`}
      >
        {ACM_SHELL_ZONE_KIND_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.labelRo}
          </option>
        ))}
      </select>
      {zone.kind === "oracal_651" ? (
        <div className="grid grid-cols-2 gap-2">
          <label className="block text-[10px] text-slate-500">
            Cod Oracal 651
            <input
              className="mt-0.5 w-full rounded border border-[#2A3548] bg-[#111827] px-2 py-1 text-[12px] text-slate-100"
              value={zone.color_code}
              onChange={(e) =>
                onChange({ ...zone, color_code: e.target.value.trim() })
              }
              placeholder="ex. 021"
              data-testid="intake-v6-acm-shell-oracal-code"
            />
          </label>
          <label className="block text-[10px] text-slate-500">
            Lățime rolă
            <select
              className="mt-0.5 w-full rounded border border-[#2A3548] bg-[#111827] px-2 py-1 text-[12px] text-slate-100"
              value={zone.roll_width_mm}
              onChange={(e) =>
                onChange({
                  ...zone,
                  roll_width_mm: Number(e.target.value) as 1000 | 1260,
                })
              }
            >
              {INTAKE_V4_ORACAL_FACE_ROLL_WIDTH_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}
      {zone.kind === "print_laminate" ? (
        <label className="block text-[10px] text-slate-500">
          Lățime rolă print+lam
          <select
            className="mt-0.5 w-full rounded border border-[#2A3548] bg-[#111827] px-2 py-1 text-[12px] text-slate-100"
            value={zone.roll_width_mm}
            onChange={(e) =>
              onChange({
                ...zone,
                roll_width_mm: Number(e.target.value) as 1050 | 1320 | 1500,
              })
            }
          >
            {PRINT_LAMINATION_ROLL_WIDTH_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      ) : null}
    </div>
  );
}
export default function IntakeV6AcmShellFinishPanel({
  finishSetup,
  onApplyFinishPatch,
  hideConfirmButton = false,
}: Props) {
  const instance = useMemo(
    () => resolveAcmPanelInstance(finishSetup).instance,
    [finishSetup],
  );
  const persisted = useMemo(
    () =>
      instance
        ? readAcmShellFinishFromInstance(instance)
        : normalizeAcmShellFinish(null),
    [instance],
  );
  const [draft, setDraft] = useState<AcmShellFinishContract>(persisted);
  const [atelierOpen, setAtelierOpen] = useState(false);
  useEffect(() => {
    setDraft(persisted);
  }, [persisted]);
  const applyMode: FoilApplyMode = shellNeedsFoil(draft) ? "after_frame" : "none";
  const faceOn = zoneNeedsFoil(draft.face);
  const volumeOn = zoneNeedsFoil(draft.volume);
  const apply = (next: AcmShellFinishContract, confirm = false) => {
    const normalized = normalizeAcmShellFinish(next);
    setDraft(normalized);
    const patch = buildAcmPanelShellFinishPatch({
      finishSetup,
      shellFinish: normalized,
      confirm,
    });
    if (patch) onApplyFinishPatch(patch);
  };
  const setApplyMode = (mode: FoilApplyMode) => {
    if (mode === "none") {
      apply({
        ...draft,
        face: defaultAcmShellZone("stock_plate"),
        volume: defaultAcmShellZone("stock_plate"),
        foil_strategy: null,
        operator_confirmed: false,
      });
      return;
    }
    const face = faceOn || volumeOn ? draft.face : defaultAcmShellZone("oracal_651");
    const volume = faceOn || volumeOn ? draft.volume : defaultAcmShellZone("stock_plate");
    apply({
      ...draft,
      face,
      volume,
      foil_strategy: draft.foil_strategy ?? { mode: "face_plus_first_fold" },
      operator_confirmed: false,
    });
  };
  const setZoneOn = (zoneId: "face" | "volume", on: boolean) => {
    const nextFace =
      zoneId === "face"
        ? on
          ? preserveOrDefaultFoilZone(draft.face)
          : defaultAcmShellZone("stock_plate")
        : draft.face;
    const nextVolume =
      zoneId === "volume"
        ? on
          ? preserveOrDefaultFoilZone(draft.volume)
          : defaultAcmShellZone("stock_plate")
        : draft.volume;
    if (!zoneNeedsFoil(nextFace) && !zoneNeedsFoil(nextVolume)) {
      apply({
        ...draft,
        face: nextFace,
        volume: nextVolume,
        foil_strategy: null,
        operator_confirmed: false,
      });
      return;
    }
    apply({
      ...draft,
      face: nextFace,
      volume: nextVolume,
      foil_strategy: draft.foil_strategy ?? { mode: "face_plus_first_fold" },
      operator_confirmed: false,
    });
  };
  if (!instance) {
    return (
      <p className="text-[11px] text-slate-500">Confirmă panoul înainte de finisaj.</p>
    );
  }
  return (
    <div className="space-y-3" data-testid="intake-v6-acm-shell-finish-panel">
      <label className="block text-[11px] text-slate-400">
        Cum aplici folia
        <select
          className="mt-0.5 w-full rounded border border-[#2A3548] bg-[#111827] px-2 py-1.5 text-[12px] text-slate-100"
          value={applyMode}
          onChange={(e) => setApplyMode(e.target.value as FoilApplyMode)}
          data-testid="intake-v6-acm-shell-apply-mode"
        >
          <option value="after_frame">După cadru</option>
          <option value="none">Fără colant</option>
        </select>
      </label>
      {applyMode === "after_frame" ? (
        <div className="space-y-2">
          <p className="text-[11px] text-slate-400">Unde aplici</p>
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-[12px] text-slate-200">
              <input
                type="checkbox"
                checked={faceOn}
                onChange={(e) => setZoneOn("face", e.target.checked)}
                data-testid="intake-v6-acm-shell-apply-face"
              />
              Față
            </label>
            <label className="flex items-center gap-2 text-[12px] text-slate-200">
              <input
                type="checkbox"
                checked={volumeOn}
                onChange={(e) => setZoneOn("volume", e.target.checked)}
                data-testid="intake-v6-acm-shell-apply-volume"
              />
              Cant (volum)
            </label>
          </div>
          <p className="text-[10px] text-slate-500">Serie: Oracal 651 · restul în atelier</p>
        </div>
      ) : (
        <p className="text-[11px] text-slate-400">Vopsire șuruburi la culoarea plăcii.</p>
      )}
      <details
        className="rounded border border-[#2A3548]/50 bg-[#0A0F1A]/30"
        open={atelierOpen}
        onToggle={(e) => setAtelierOpen((e.target as HTMLDetailsElement).open)}
        data-testid="intake-v6-acm-shell-atelier-details"
      >
        <summary className="cursor-pointer select-none px-2 py-1.5 text-[11px] text-slate-400">
          Detalii atelier
        </summary>
        {atelierOpen ? (
          <div className="space-y-2 border-t border-[#2A3548]/40 px-2 py-2">
            <AtelierZoneFields
              zoneId="face"
              labelRo="Față"
              zone={draft.face}
              onChange={(face) => apply({ ...draft, face, operator_confirmed: false })}
            />
            <AtelierZoneFields
              zoneId="volume"
              labelRo="Cant (volum)"
              zone={draft.volume}
              onChange={(volume) => apply({ ...draft, volume, operator_confirmed: false })}
            />
            {shellNeedsFoil(draft) ? (
              <div className="space-y-1.5 rounded border border-[#2A3548]/60 px-2 py-2">
                <p className="text-[11px] font-semibold text-slate-300">Strategie folie</p>
                <select
                  className="w-full rounded border border-[#2A3548] bg-[#111827] px-2 py-1.5 text-[12px] text-slate-100"
                  value={draft.foil_strategy?.mode ?? "face_plus_first_fold"}
                  onChange={(e) => {
                    const mode = e.target.value as AcmShellFoilStrategyMode;
                    const foil_strategy =
                      mode === "face_multi_piece"
                        ? {
                            mode: "face_multi_piece" as const,
                            piece_count:
                              draft.foil_strategy &&
                              draft.foil_strategy.mode === "face_multi_piece"
                                ? draft.foil_strategy.piece_count
                                : 2,
                            client_informed:
                              draft.foil_strategy &&
                              draft.foil_strategy.mode === "face_multi_piece"
                                ? draft.foil_strategy.client_informed
                                : false,
                          }
                        : mode === "face_one_piece_volume_separate"
                          ? { mode: "face_one_piece_volume_separate" as const }
                          : { mode: "face_plus_first_fold" as const };
                    apply({ ...draft, foil_strategy, operator_confirmed: false });
                  }}
                  data-testid="intake-v6-acm-shell-foil-strategy"
                >
                  {ACM_SHELL_FOIL_STRATEGY_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.labelRo}
                    </option>
                  ))}
                </select>
                {draft.foil_strategy?.mode === "face_multi_piece" ? (
                  <div className="grid grid-cols-2 gap-2">
                    <label className="block text-[10px] text-slate-500">
                      Nr. bucăți
                      <input
                        type="number"
                        min={2}
                        className="mt-0.5 w-full rounded border border-[#2A3548] bg-[#111827] px-2 py-1 text-[12px] text-slate-100"
                        value={draft.foil_strategy.piece_count}
                        onChange={(e) =>
                          apply({
                            ...draft,
                            foil_strategy: {
                              mode: "face_multi_piece",
                              piece_count: Math.max(2, Number(e.target.value) || 2),
                              client_informed:
                                draft.foil_strategy!.mode === "face_multi_piece"
                                  ? draft.foil_strategy.client_informed
                                  : false,
                            },
                            operator_confirmed: false,
                          })
                        }
                      />
                    </label>
                    <label className="flex items-end gap-2 pb-1 text-[11px] text-slate-300">
                      <input
                        type="checkbox"
                        checked={draft.foil_strategy.client_informed}
                        onChange={(e) =>
                          apply({
                            ...draft,
                            foil_strategy: {
                              mode: "face_multi_piece",
                              piece_count:
                                draft.foil_strategy!.mode === "face_multi_piece"
                                  ? draft.foil_strategy.piece_count
                                  : 2,
                              client_informed: e.target.checked,
                            },
                            operator_confirmed: false,
                          })
                        }
                      />
                      Client informat
                    </label>
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}
      </details>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-[11px] text-slate-400" data-testid="intake-v6-acm-shell-finish-summary">
          {summarizeAcmShellFinishOperatorRo(normalizeAcmShellFinish(draft))}
          {intakeV6ShowOperatorConfigStatusBadges() ? (
            draft.operator_confirmed ? (
              <span className="ml-2 text-emerald-300">· confirmat</span>
            ) : hideConfirmButton ? (
              <span className="ml-2 text-slate-500">· se confirmă cu panoul</span>
            ) : (
              <span className="ml-2 text-amber-300/80">· neconfirmat</span>
            )
          ) : null}
        </p>
        {hideConfirmButton ? null : (
          <button
            type="button"
            className="rounded border border-emerald-500/40 bg-emerald-500/15 px-2.5 py-1 text-[11px] font-semibold text-emerald-100"
            onClick={() => apply(draft, true)}
            data-testid="intake-v6-acm-shell-finish-confirm"
          >
            Confirmă finisaj
          </button>
        )}
      </div>
    </div>
  );
}
