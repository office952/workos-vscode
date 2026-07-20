/**
 * Compact production DXF attachment UI for AcmPanel inspector.
 * Technical status only — no money.
 */

import { useMemo, useState } from "react";
import {
  activeProductionGeometryAttachments,
  uploadAcmPanelProductionDxf,
} from "@/lib/intakeV6/acmPanel/productionGeometryApi";

type Props = {
  workspaceId: string | null | undefined;
  componentInstanceId: string;
  instance: Record<string, unknown>;
  onBound: () => void;
};

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    measured: "măsurat",
    measured_with_warnings: "măsurat (avertismente)",
    stale: "stale — reîncarcă DXF",
    invalid: "invalid",
    semantic_mapping_required: "mapping ACI necesar",
    uploaded: "încărcat",
    unavailable: "indisponibil",
    proxy_rectangular: "proxy",
    no_attachment: "fără atașament",
  };
  return map[status] || status;
}

export default function AcmPanelProductionGeometryBlock({
  workspaceId,
  componentInstanceId,
  instance,
  onBound,
}: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastPreview, setLastPreview] = useState<Record<string, unknown> | null>(null);

  const panels = useMemo(() => {
    const geo = instance.geometry as { panels?: Array<{ panel_id?: string }> } | undefined;
    const list = geo?.panels;
    if (!Array.isArray(list) || !list.length) return [{ panel_id: "" }];
    return list.map((p) => ({ panel_id: String(p.panel_id || "") }));
  }, [instance]);

  const [panelId, setPanelId] = useState<string>(() => panels[0]?.panel_id || "");

  const active = activeProductionGeometryAttachments(instance);
  const forPanel = active.filter((a) => {
    const pid = a.panel_id == null || a.panel_id === "" ? "" : String(a.panel_id);
    const sel = panelId || "";
    return pid === sel || (active.length === 1 && !pid);
  });
  const current = forPanel[0] || active[0] || null;

  async function onFile(file: File | null) {
    if (!file || !workspaceId) return;
    setBusy(true);
    setError(null);
    try {
      const result = await uploadAcmPanelProductionDxf({
        workspaceId,
        file,
        componentInstanceId,
        panelId: panelId || null,
        geometryRole: "production_geometry",
        bind: true,
      });
      setLastPreview((result.measurement_preview as Record<string, unknown>) || null);
      onBound();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload eșuat");
    } finally {
      setBusy(false);
    }
  }

  const snap = (current?.metrics_snapshot as Record<string, unknown> | undefined) || lastPreview;
  const mStatus = String(current?.measurement_status || snap?.measurement_status || "no_attachment");

  return (
    <div
      className="mt-3 space-y-2 rounded border border-[#2A3548]/50 bg-[#0A0F1A]/40 px-2 py-2"
      data-testid="intake-v6-acm-production-geometry"
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] font-semibold text-slate-200">Geometrie producție (DXF)</p>
        <span
          className="rounded border border-slate-600/40 px-1.5 py-0.5 text-[10px] text-slate-400"
          data-testid="intake-v6-acm-pg-status"
        >
          {statusLabel(mStatus)}
        </span>
      </div>

      {panels.length > 1 ? (
        <label className="block text-[10px] text-slate-500">
          Panou
          <select
            className="mt-0.5 w-full rounded border border-[#2A3548] bg-[#111827] px-1.5 py-1 text-[11px] text-slate-200"
            data-testid="intake-v6-acm-pg-panel"
            value={panelId}
            onChange={(e) => setPanelId(e.target.value)}
          >
            {panels.map((p) => (
              <option key={p.panel_id || "none"} value={p.panel_id}>
                {p.panel_id || "assembly / default"}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      <p className="text-[10px] text-slate-500" data-testid="intake-v6-acm-pg-filename">
        Fișier: {String(current?.original_filename || current?.filename || "—")}
      </p>
      <p className="text-[10px] text-slate-500">Rol: production_geometry</p>

      {snap ? (
        <div className="grid grid-cols-2 gap-1 text-[10px] text-slate-300" data-testid="intake-v6-acm-pg-metrics">
          <span>CUT: {snap.cut_length_ml ?? "—"} ml</span>
          <span>V tot: {snap.v_groove_total_ml ?? "—"} ml</span>
          <span>V L1: {snap.v_groove_l1_ml ?? "—"} ml</span>
          <span>V L2: {snap.v_groove_l2_ml ?? "—"} ml</span>
        </div>
      ) : null}

      {mStatus === "stale" ? (
        <p className="text-[10px] text-amber-200" data-testid="intake-v6-acm-pg-stale">
          Configurația s-a schimbat — măsurarea este stale. Reîncarcă DXF.
        </p>
      ) : null}

      {Array.isArray(current?.warnings) && (current.warnings as string[]).length ? (
        <ul className="list-inside list-disc text-[10px] text-amber-200/90" data-testid="intake-v6-acm-pg-warnings">
          {(current.warnings as string[]).slice(0, 4).map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      ) : null}

      {error ? (
        <p className="text-[10px] text-rose-300" data-testid="intake-v6-acm-pg-error">
          {error}
        </p>
      ) : null}

      <label className="inline-flex cursor-pointer items-center gap-2 rounded border border-sky-500/30 px-2 py-1 text-[11px] text-sky-200">
        <input
          type="file"
          accept=".dxf,application/dxf,image/vnd.dxf"
          className="hidden"
          data-testid="intake-v6-acm-pg-file"
          disabled={busy || !workspaceId}
          onChange={(e) => {
            const f = e.target.files?.[0] || null;
            e.target.value = "";
            void onFile(f);
          }}
        />
        {busy ? "Se încarcă…" : current ? "Înlocuiește DXF" : "Încarcă DXF"}
      </label>
      {!workspaceId ? (
        <p className="text-[10px] text-slate-500">Workspace indisponibil pentru upload.</p>
      ) : null}
    </div>
  );
}
