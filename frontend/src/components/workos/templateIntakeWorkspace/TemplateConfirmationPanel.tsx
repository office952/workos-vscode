import { ArrowRight, CheckCircle2 } from "lucide-react";
import { INTAKE_SECTION_IDS } from "@/lib/intakeActionSummary";

export interface TemplateConfirmationPanelProps {
  templateCode: string;
  confirmed: boolean;
  confirming: boolean;
  readOnly: boolean;
  onConfirm: () => void;
}

export default function TemplateConfirmationPanel({
  templateCode,
  confirmed,
  confirming,
  readOnly,
  onConfirm,
}: TemplateConfirmationPanelProps) {
  return (
    <div
      id={INTAKE_SECTION_IDS.template}
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-3 scroll-mt-4"
      data-testid="volumetric-template-step"
    >
      {confirmed ? (
        <p className="text-[12px] text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            Template <span className="font-mono font-semibold">{templateCode}</span>
          </span>
        </p>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-[12px] text-slate-300">Confirmă template-ul produsului.</p>
          <button
            type="button"
            disabled={confirming || readOnly}
            onClick={() => void onConfirm()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[12px] font-bold bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50"
          >
            {confirming ? "Se salvează…" : "Confirmă template"}
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
