import {
  PATHWAY_OPTIONS,
  pathwayHint,
  type VolumetricIntakePathway,
} from "@/lib/volumetricIntakePathway";
import InfoHint from "@/components/workos/templateIntakeWorkspace/InfoHint";
import { FileImage, PenLine, Zap } from "lucide-react";

const ICONS: Record<VolumetricIntakePathway, typeof FileImage> = {
  vector: FileImage,
  manual: PenLine,
  quick_estimate: Zap,
};

export interface IntakePathwaySelectorProps {
  value: VolumetricIntakePathway;
  onChange: (pathway: VolumetricIntakePathway) => void;
  readOnly?: boolean;
}

export default function IntakePathwaySelector({
  value,
  onChange,
  readOnly = false,
}: IntakePathwaySelectorProps) {
  return (
    <div
      className="rounded-lg border border-blue-900/40 bg-blue-950/15 p-4 space-y-3"
      data-testid="intake-pathway-selector"
    >
      <div className="flex items-center gap-1.5">
        <p className="text-[12px] font-semibold text-slate-100">
          Cum introduci produsul?
        </p>
        <InfoHint label="Despre calea de introducere">
          Alegerea reduce câmpurile afișate. Datele deja salvate nu se șterg la schimbarea
          căii. {pathwayHint(value)}
        </InfoHint>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        {PATHWAY_OPTIONS.map((opt) => {
          const active = value === opt.id;
          const Icon = ICONS[opt.id];
          return (
            <button
              key={opt.id}
              type="button"
              disabled={readOnly}
              data-testid={`intake-pathway-${opt.id}`}
              onClick={() => onChange(opt.id)}
              className={`text-left rounded-lg border p-3 transition-colors disabled:opacity-60 ${
                active
                  ? "border-blue-500/60 bg-blue-950/40 ring-1 ring-blue-500/30"
                  : "border-wo-border-strong bg-[#0f1524] hover:border-slate-500"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon
                  className={`w-4 h-4 shrink-0 ${active ? "text-blue-400" : "text-slate-500"}`}
                />
                <p className="text-[12px] font-semibold text-slate-100">{opt.title}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
