/**
 * Compact production DXF attachment strip for AcmPanel inspector.
 * Technical status only — no money.
 */

import { useMemo, useState } from "react";
import {
  activeProductionGeometryAttachments,
  uploadAcmPanelProductionDxf,
} from "@/lib/intakeV6/acmPanel/productionGeometryApi";
import { intakeV6ShowOperatorConfigStatusBadges } from "@/lib/intakeV6/intakeV6OperatorConfigStatusChrome";

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
    commercial_deduced: "deducere comercială",
    commercial_deduced_with_assumptions: "deducere (asumpții)",
    no_attachment: "fără atașament",
  };
  return map[status] || status;
}

function statusTone(status: string): string {
  if (status === "stale" || status === "invalid" || status === "semantic_mapping_required") {
    return "border-amber-500/35 bg-amber-500/10 text-amber-200/90";
  }
  if (
    status === "measured" ||
    status === "measured_with_warnings" ||
    status === "uploaded" ||
    status === "commercial_deduced" ||
    status === "commercial_deduced_with_assumptions"
  ) {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200/90";
  }
  return "border-slate-600/35 bg-slate-800/40 text-slate-400";
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
  const filename = String(current?.original_filename || current?.filename || "").trim();
  const hasFile = Boolean(filename);
  const hasMetrics = Boolean(snap);
  const hasWarnings =
    Array.isArray(current?.warnings) && (current.warnings as string[]).length > 0;
  const showDetail = hasMetrics || mStatus === "stale" || hasWarnings || Boolean(error);

  return (
    <div
      className="mt-2 border-t border-[#2A3548]/45 pt-2"
      data-testid="intake-v6-acm-production-geometry"
    >
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <span className="text-[11px] font-medium tracking-tight text-slate-300">
          DXF producție
        </span>
        {intakeV6ShowOperatorConfigStatusBadges() ? (
          <span
            className={`rounded border px-1.5 py-px text-[10px] leading-4 ${statusTone(mStatus)}`}
            data-testid="intake-v6-acm-pg-status"
          >
            {statusLabel(mStatus)}
          </span>
        ) : null}

        {panels.length > 1 ? (
          <select
            className="h-6 max-w-[9rem] truncate rounded border border-[#2A3548]/70 bg-[#111827]/80 px-1.5 text-[10px] text-slate-300"
            data-testid="intake-v6-acm-pg-panel"
            value={panelId}
            onChange={(e) => setPanelId(e.target.value)}
            aria-label="Panou"
          >
            {panels.map((p) => (
              <option key={p.panel_id || "none"} value={p.panel_id}>
                {p.panel_id || "assembly / default"}
              </option>
            ))}
          </select>
        ) : null}

        {hasFile ? (
          <span
            className="min-w-0 max-w-[12rem] truncate text-[10px] text-slate-400"
            data-testid="intake-v6-acm-pg-filename"
            title={filename}
          >
            {filename}
          </span>
        ) : (
          <span className="sr-only" data-testid="intake-v6-acm-pg-filename">
            —
          </span>
        )}

        <label
          className={`ml-auto inline-flex h-6 cursor-pointer items-center rounded border px-2 text-[10px] font-medium transition-colors ${
            busy || !workspaceId
              ? "cursor-not-allowed border-slate-600/40 text-slate-500"
              : "border-sky-500/35 bg-sky-500/10 text-sky-200 hover:border-sky-400/50 hover:bg-sky-500/15"
          }`}
        >
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
          {busy ? "Se încarcă…" : current ? "Înlocuiește" : "Încarcă DXF"}
        </label>
      </div>

      {!hasFile ? (
        <p className="mt-0.5 text-[10px] leading-4 text-slate-500/90">
          opțional · măsurători atelier
          {!workspaceId ? " · workspace indisponibil" : null}
        </p>
      ) : null}

      {showDetail ? (
        <div className="mt-1.5 space-y-1">
          {hasMetrics ? (
            <div
              className="flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] tabular-nums text-slate-400"
              data-testid="intake-v6-acm-pg-metrics"
            >
              <span>
                CUT <span className="text-slate-300">{String(snap?.cut_length_ml ?? "—")}</span> ml
              </span>
              <span>
                V <span className="text-slate-300">{String(snap?.v_groove_total_ml ?? "—")}</span> ml
              </span>
              <span>
                L1 <span className="text-slate-300">{String(snap?.v_groove_l1_ml ?? "—")}</span>
              </span>
              <span>
                L2 <span className="text-slate-300">{String(snap?.v_groove_l2_ml ?? "—")}</span>
              </span>
            </div>
          ) : null}

          {mStatus === "stale" ? (
            <p className="text-[10px] leading-4 text-amber-200/90" data-testid="intake-v6-acm-pg-stale">
              Configurația s-a schimbat — reîncarcă DXF.
            </p>
          ) : null}

          {hasWarnings && current ? (
            <ul
              className="list-inside list-disc text-[10px] leading-4 text-amber-200/80"
              data-testid="intake-v6-acm-pg-warnings"
            >
              {(current.warnings as string[]).slice(0, 4).map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          ) : null}

          {error ? (
            <p className="text-[10px] leading-4 text-rose-300" data-testid="intake-v6-acm-pg-error">
              {error}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}