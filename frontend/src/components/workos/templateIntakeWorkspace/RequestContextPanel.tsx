import { useNavigate } from "react-router-dom";
import { ArrowLeft, Layers } from "lucide-react";
import {
  type DeliveryType,
  deliveryTypeLabels,
  type IntakeRequest,
  type IntakeStatus,
} from "@/lib/mockData";

const statusConfig: Record<IntakeStatus, { label: string; cls: string }> = {
  new: { label: "Nou", cls: "bg-slate-700/60 text-slate-300 border-slate-600" },
  in_review: { label: "În Analiză", cls: "bg-blue-900/40 text-blue-300 border-blue-700" },
  needs_info: { label: "Lipsă Info", cls: "bg-amber-900/40 text-amber-300 border-amber-700" },
  ready_for_quote: {
    label: "Gata pt. Ofertă",
    cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700",
  },
  blocked: { label: "Blocat", cls: "bg-red-900/40 text-red-300 border-red-700" },
  cancelled: { label: "Anulat", cls: "bg-slate-800/60 text-slate-400 border-slate-600" },
};

export interface RequestContextPanelProps {
  request: IntakeRequest;
  source: string;
  assignedTo: string;
  setAssignedTo: (value: string) => void;
  selectedDeliveryType: DeliveryType;
  onDeliveryTypeChange: (dt: DeliveryType) => void;
  onAssignedBlur: () => void;
  templateFamilyLabel?: string;
  variant?: "default" | "compact";
  deliveryStageNote?: string | null;
}

export default function RequestContextPanel({
  request,
  source,
  assignedTo,
  setAssignedTo,
  selectedDeliveryType,
  onDeliveryTypeChange,
  onAssignedBlur,
  templateFamilyLabel = "Litere volumetrice",
  variant = "default",
  deliveryStageNote,
}: RequestContextPanelProps) {
  const navigate = useNavigate();
  const sCfg = statusConfig[request.status];
  const compact = variant === "compact";

  return (
    <div
      className={`bg-[#111827] border border-[#1E293B] rounded-lg ${compact ? "p-3" : "p-4"}`}
      data-testid="request-context-panel"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 flex-wrap min-w-0">
          <h1 className="text-[17px] font-bold text-slate-100">{request.id}</h1>
          <span
            className={`inline-flex px-2 py-0.5 text-[10px] font-semibold rounded border ${sCfg.cls}`}
          >
            {sCfg.label}
          </span>
          <span className="inline-flex items-center gap-1 text-[10px] text-slate-400">
            <Layers className="w-3 h-3 text-purple-400" />
            {templateFamilyLabel}
          </span>
        </div>
        <button
          type="button"
          onClick={() => navigate("/intake")}
          className="inline-flex items-center gap-1.5 px-2 py-1 text-[11px] text-slate-500 hover:text-slate-200"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Lista
        </button>
      </div>

      <div
        className={`grid gap-x-3 gap-y-2 text-[12px] ${
          compact ? "grid-cols-1" : "grid-cols-2 md:grid-cols-4"
        }`}
      >
        <div>
          <p className="text-[10px] text-slate-500">Client</p>
          <p className="text-slate-100 font-medium truncate">{request.client}</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500">Contact</p>
          <p className="text-slate-300 truncate">{request.contactPerson}</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500">Asignat</p>
          {source === "mock" ? (
            <p className="text-slate-300 truncate">{assignedTo}</p>
          ) : (
            <input
              type="text"
              value={assignedTo === "—" ? "" : assignedTo}
              onChange={(e) => setAssignedTo(e.target.value)}
              onBlur={() => void onAssignedBlur()}
              placeholder="Operator"
              className="w-full bg-[#0D1321] border border-[#2A3548] rounded px-2 py-0.5 text-[11px] text-slate-200"
            />
          )}
        </div>
        <div>
          <p className="text-[10px] text-slate-500 mb-0.5">Livrare</p>
          <select
            value={selectedDeliveryType}
            disabled={source === "mock"}
            onChange={(e) => void onDeliveryTypeChange(e.target.value as DeliveryType)}
            className="w-full bg-[#0D1321] border border-[#2A3548] rounded px-2 py-0.5 text-[11px] text-slate-200"
          >
            {(Object.keys(deliveryTypeLabels) as DeliveryType[]).map((dt) => (
              <option key={dt} value={dt}>
                {deliveryTypeLabels[dt]}
              </option>
            ))}
          </select>
          {deliveryStageNote && (
            <p
              className="mt-1 text-[10px] text-slate-500 leading-snug"
              data-testid="delivery-stage-note"
            >
              {deliveryStageNote}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
